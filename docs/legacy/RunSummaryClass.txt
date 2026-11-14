import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional


class RunSummary:
    """
    Build a human-friendly summary from a JSONL run manifest.

    Outputs:
    - summary_run_<runid>.json
    - summary_run_<runid>.txt
    """

    TAG_PATTERN = re.compile(r"\[(g|d)-(.*?)\]", re.IGNORECASE)

    def __init__(self, manifest_path: str):
        if not manifest_path or not str(manifest_path).strip():
            raise ValueError("manifest_path cannot be empty")

        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        self.report_dir = os.path.dirname(self.manifest_path)
        self.run_id = self._extract_run_id(self.manifest_path)

    def build(self) -> Dict[str, Any]:
        latest_by_movie = self._load_latest_records()

        summary: Dict[str, Any] = {
            "run_id": self.run_id,
            "manifest_path": self.manifest_path,
            "totals": {
                "total_movies_seen": 0,
                "moved_new": 0,
                "updated_existing": 0,
                "skipped_existing": 0,
                "skipped_unknown_genre": 0,
                "conflicts": 0,
                "errors": 0,
                "dry_run_only": 0,
            },
            "groups": {
                "moved_new": [],
                "updated_existing": [],
                "skipped_existing": [],
                "skipped_unknown_genre": [],
                "conflicts": [],
                "errors": [],
                "dry_run_only": [],
            },
            "by_genre": defaultdict(list),
        }

        for movie_id, record in latest_by_movie.items():
            status = str(record.get("status", "unknown"))
            item = self._normalize_record(movie_id, record)

            summary["totals"]["total_movies_seen"] += 1

            if status == "verified_and_source_deleted":
                move_kind = item.get("move_kind", "new")
                if move_kind == "updated":
                    summary["totals"]["updated_existing"] += 1
                    summary["groups"]["updated_existing"].append(item)
                else:
                    summary["totals"]["moved_new"] += 1
                    summary["groups"]["moved_new"].append(item)

                genre = item.get("final_genre") or "UNKNOWN"
                summary["by_genre"][genre].append(item)

            elif status == "skipped_existing_in_vose_precheck":
                summary["totals"]["skipped_existing"] += 1
                summary["groups"]["skipped_existing"].append(item)

            elif status == "skipped_existing_conflict":
                summary["totals"]["conflicts"] += 1
                summary["groups"]["conflicts"].append(item)

            elif status == "skipped_unknown_genre":
                summary["totals"]["skipped_unknown_genre"] += 1
                summary["groups"]["skipped_unknown_genre"].append(item)

            elif status.startswith("dry_run_"):
                summary["totals"]["dry_run_only"] += 1
                summary["groups"]["dry_run_only"].append(item)

            elif status == "conflict_or_error":
                error_text = str(record.get("error", "")).lower()
                if "conflict" in error_text:
                    summary["totals"]["conflicts"] += 1
                    summary["groups"]["conflicts"].append(item)
                else:
                    summary["totals"]["errors"] += 1
                    summary["groups"]["errors"].append(item)

            else:
                # Catch-all: if needed later, you can create a new group
                pass

        # Convert defaultdict to plain dict
        summary["by_genre"] = dict(summary["by_genre"])
        return summary

    def write_files(self) -> Dict[str, str]:
        summary = self.build()

        json_path = os.path.join(self.report_dir, f"summary_run_{self.run_id}.json")
        txt_path = os.path.join(self.report_dir, f"summary_run_{self.run_id}.txt")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(self._render_text_summary(summary))

        return {
            "json": json_path,
            "txt": txt_path,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _extract_run_id(self, manifest_path: str) -> str:
        file_name = os.path.basename(manifest_path)
        prefix = "manifest_run_"
        suffix = ".jsonl"
        if file_name.startswith(prefix) and file_name.endswith(suffix):
            return file_name[len(prefix):-len(suffix)]
        return "unknown"

    def _load_latest_records(self) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                movie_id = record.get("movie_id")
                if not movie_id:
                    continue

                latest[str(movie_id)] = record

        return latest

    def _normalize_record(self, movie_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        source_path = record.get("source_path") or record.get("raw_path") or ""
        temp_path = record.get("temp_path") or ""
        destination = record.get("destination") or ""
        original_name = record.get("original_name") or movie_id
        clean_name = record.get("clean_name") or self._strip_tags(original_name)
        removed_tags = record.get("removed_tags") or self._extract_tags(original_name)
        final_genre = record.get("final_genre") or self._infer_genre_from_destination(destination)

        move_kind = record.get("move_kind")
        if not move_kind:
            if record.get("updated_existing") is True:
                move_kind = "updated"
            else:
                move_kind = "new"

        return {
            "movie_id": movie_id,
            "status": record.get("status"),
            "original_name": original_name,
            "clean_name": clean_name,
            "removed_tags": removed_tags,
            "source_path": source_path,
            "temp_path": temp_path,
            "destination": destination,
            "final_genre": final_genre,
            "move_kind": move_kind,
            "error": record.get("error", ""),
        }

    def _extract_tags(self, text: str) -> Dict[str, List[str]]:
        tags = {"genre_tags": [], "director_tags": []}
        for tag_type, value in self.TAG_PATTERN.findall(text or ""):
            if tag_type.lower() == "g":
                tags["genre_tags"].append(value.strip())
            elif tag_type.lower() == "d":
                tags["director_tags"].append(value.strip())
        return tags

    def _strip_tags(self, text: str) -> str:
        cleaned = re.sub(r"\[.*?\]", "", text or "")
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip()

    def _infer_genre_from_destination(self, destination: str) -> str:
        if not destination:
            return "UNKNOWN"

        parts = os.path.normpath(destination).split(os.sep)
        if len(parts) >= 2:
            # Usually ...\VOSE\ACTION\Movie Name
            return parts[-2]
        return "UNKNOWN"

    def _render_text_summary(self, summary: Dict[str, Any]) -> str:
        lines: List[str] = []

        lines.append(f"RUN SUMMARY: {summary['run_id']}")
        lines.append(f"Manifest: {summary['manifest_path']}")
        lines.append("")

        totals = summary["totals"]
        lines.append("TOTALS")
        lines.append(f"- Total movies seen      : {totals['total_movies_seen']}")
        lines.append(f"- Moved as new           : {totals['moved_new']}")
        lines.append(f"- Updated existing       : {totals['updated_existing']}")
        lines.append(f"- Skipped existing       : {totals['skipped_existing']}")
        lines.append(f"- Skipped unknown genre  : {totals['skipped_unknown_genre']}")
        lines.append(f"- Conflicts              : {totals['conflicts']}")
        lines.append(f"- Errors                 : {totals['errors']}")
        lines.append(f"- Dry-run only           : {totals['dry_run_only']}")
        lines.append("")

        def add_group(title: str, items: List[Dict[str, Any]]) -> None:
            lines.append(title)
            if not items:
                lines.append("  (none)")
                lines.append("")
                return

            for item in items:
                lines.append(f"- {item['clean_name']}")
                if item.get("source_path"):
                    lines.append(f"    source      : {item['source_path']}")
                if item.get("destination"):
                    lines.append(f"    destination : {item['destination']}")
                if item.get("final_genre"):
                    lines.append(f"    final genre : {item['final_genre']}")
                if item.get("removed_tags"):
                    genre_tags = item["removed_tags"].get("genre_tags", [])
                    director_tags = item["removed_tags"].get("director_tags", [])
                    if genre_tags or director_tags:
                        lines.append(
                            f"    removed tags: genre={genre_tags or []}, director={director_tags or []}"
                        )
                if item.get("move_kind"):
                    lines.append(f"    move kind   : {item['move_kind']}")
                if item.get("error"):
                    lines.append(f"    error       : {item['error']}")
            lines.append("")

        add_group("MOVED AS NEW", summary["groups"]["moved_new"])
        add_group("UPDATED EXISTING", summary["groups"]["updated_existing"])
        add_group("SKIPPED EXISTING", summary["groups"]["skipped_existing"])
        add_group("CONFLICTS", summary["groups"]["conflicts"])
        add_group("ERRORS", summary["groups"]["errors"])

        lines.append("BY GENRE")
        by_genre = summary["by_genre"]
        if not by_genre:
            lines.append("  (none)")
        else:
            for genre, items in sorted(by_genre.items()):
                lines.append(f"- {genre}: {len(items)}")
        lines.append("")

        return "\n".join(lines)