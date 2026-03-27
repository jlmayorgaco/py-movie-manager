import json
import os
import time
from typing import Any, Dict, Optional


class RunManifest:
    """
    Durable JSONL manifest to track processed movie folders.

    Design goals:
    - Safe against os.chdir() by resolving paths to absolute paths on init.
    - Append-only JSONL file for easy auditability.
    - In-memory latest-state index for fast resume checks.
    - Aligned with the actual statuses emitted by MovieManagerClass.py.
    """

    COMPLETED_STATES = {
        "verified",
        "source_deleted",
        "skipped",
        "verified_and_source_deleted",
        "skipped_unknown_genre",
        "skipped_existing_in_vose_precheck",
        "skipped_existing_conflict",
    }

    def __init__(self, manifest_dir: str, run_id: str):
        if not manifest_dir or not str(manifest_dir).strip():
            raise ValueError("manifest_dir cannot be empty")

        if not run_id or not str(run_id).strip():
            raise ValueError("run_id cannot be empty")

        self.manifest_dir = os.path.abspath(str(manifest_dir).strip())
        self.run_id = str(run_id).strip()
        self.manifest_path = os.path.join(
            self.manifest_dir,
            f"manifest_run_{self.run_id}.jsonl",
        )

        os.makedirs(self.manifest_dir, exist_ok=True)

        # Latest known state by movie_id
        self._state_map: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Load / read helpers
    # ------------------------------------------------------------------
    def load_existing(self, path: Optional[str] = None) -> None:
        """
        Load an existing manifest into memory.

        If path is None, load this instance's manifest file.
        """
        target_path = os.path.abspath(path) if path else self.manifest_path

        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Manifest not found: {target_path}")

        self._state_map.clear()

        with open(target_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    # Ignore malformed lines instead of crashing the whole load
                    continue

                movie_id = record.get("movie_id")
                if movie_id:
                    self._state_map[str(movie_id)] = record

    def get_state(self, movie_id: str) -> Optional[str]:
        """
        Get the latest recorded state of a movie folder.
        """
        record = self._state_map.get(str(movie_id))
        return record.get("status") if record else None

    def get_record(self, movie_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest full record for a movie_id.
        """
        return self._state_map.get(str(movie_id))

    def get_manifest_path(self) -> str:
        return self.manifest_path

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------
    def record_state(
        self,
        movie_id: str,
        state: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append a state transition for a movie folder to the manifest.
        """
        movie_id = str(movie_id).strip()
        state = str(state).strip()

        if not movie_id:
            raise ValueError("movie_id cannot be empty")

        if not state:
            raise ValueError("state cannot be empty")

        os.makedirs(self.manifest_dir, exist_ok=True)

        record: Dict[str, Any] = {
            "movie_id": movie_id,
            "status": state,
            "timestamp": time.time(),
        }

        if details:
            record.update(details)

        self._state_map[movie_id] = record

        with open(self.manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

    # ------------------------------------------------------------------
    # Resume helpers
    # ------------------------------------------------------------------
    def is_completed(self, movie_id: str) -> bool:
        """
        Check if a movie folder reached a terminal/completed state in a prior run.

        Note:
        We intentionally do NOT treat dry-run states as completed.
        """
        state = self.get_state(movie_id)
        return state in self.COMPLETED_STATES

    def is_terminal(self, movie_id: str) -> bool:
        """
        Alias of is_completed for readability.
        """
        return self.is_completed(movie_id)

    def count_by_status(self) -> Dict[str, int]:
        """
        Return a summary count of latest statuses currently loaded in memory.
        """
        counts: Dict[str, int] = {}
        for record in self._state_map.values():
            status = str(record.get("status", "unknown"))
            counts[status] = counts.get(status, 0) + 1
        return counts