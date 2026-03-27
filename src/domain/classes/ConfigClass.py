import json
import os
from enum import EnumMeta
from typing import Iterable, List, Union

from src.domain.interfaces.IConfigInterface import IConfig
from config.GenresConfig import GenresEnum


class Config(IConfig):
    """
    Config: manages directory paths, genres, execution flags, and runtime options.
    """

    VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
    VALID_SORT_MODES = {"name", "date"}

    def __init__(self, config_file: str = "config/config.json"):
        self._directory_raw: str = ""
        self._directory_temp: str = ""
        self._directory_vose: str = ""
        self._genres: List[GenresEnum] = []
        self._dry_run: bool = False

        # Runtime / CLI flags
        self._preflight: bool = False
        self._plan: bool = False
        self._resume: bool = False
        self._limit: int = 0
        self._log_level: str = "INFO"
        self._report_dir: str = "reports"
        self._workers: int = 1
        self._stop_on_conflict: bool = False
        self._continue_on_error: bool = False
        self._sort: str = "name"

        self._config_file = config_file
        self._load_from_json()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _to_bool(self, value) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "y", "on"}:
                return True
            if normalized in {"false", "0", "no", "n", "off"}:
                return False

        return bool(value)

    def _to_non_negative_int(self, value, field_name: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be an integer.") from exc

        if parsed < 0:
            raise ValueError(f"{field_name} cannot be negative.")

        return parsed

    def _to_positive_int(self, value, field_name: str) -> int:
        parsed = self._to_non_negative_int(value, field_name)
        if parsed < 1:
            raise ValueError(f"{field_name} must be >= 1.")
        return parsed

    def _load_from_json(self) -> None:
        """
        Load configuration values from a JSON file.
        Missing keys keep their defaults.
        """
        if not os.path.exists(self._config_file):
            raise FileNotFoundError(f"Config file not found: {self._config_file}")

        with open(self._config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._directory_raw = str(data.get("directory_raw", self._directory_raw) or "").strip()
        self._directory_temp = str(data.get("directory_temp", self._directory_temp) or "").strip()
        self._directory_vose = str(data.get("directory_vose", self._directory_vose) or "").strip()

        self._dry_run = self._to_bool(data.get("dry_run", self._dry_run))
        self._preflight = self._to_bool(data.get("preflight", self._preflight))
        self._plan = self._to_bool(data.get("plan", self._plan))
        self._resume = self._to_bool(data.get("resume", self._resume))

        self._limit = self._to_non_negative_int(data.get("limit", self._limit), "limit")
        self._workers = self._to_positive_int(data.get("workers", self._workers), "workers")

        log_level = str(data.get("log_level", self._log_level) or "INFO").upper()
        if log_level in self.VALID_LOG_LEVELS:
            self._log_level = log_level

        sort_mode = str(data.get("sort", self._sort) or "name").lower()
        if sort_mode in self.VALID_SORT_MODES:
            self._sort = sort_mode

        report_dir = str(data.get("report_dir", self._report_dir) or "").strip()
        if report_dir:
            self._report_dir = report_dir

        self._stop_on_conflict = self._to_bool(
            data.get("stop_on_conflict", self._stop_on_conflict)
        )
        self._continue_on_error = self._to_bool(
            data.get("continue_on_error", self._continue_on_error)
        )

        # If stop_on_conflict is true, it wins over continue_on_error
        if self._stop_on_conflict:
            self._continue_on_error = False

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        genres_str = ", ".join([genre.name for genre in self._genres]) if self._genres else "Not Set"
        return (
            f"Config::Directory Source <{self._directory_raw}>\n"
            f"Config::Directory Temp <{self._directory_temp}>\n"
            f"Config::Directory Target <{self._directory_vose}>\n"
            f"Config::Dry Run <{self._dry_run}>\n"
            f"Config::Preflight <{self._preflight}>\n"
            f"Config::Plan <{self._plan}>\n"
            f"Config::Resume <{self._resume}>\n"
            f"Config::Limit <{self._limit}>\n"
            f"Config::Log Level <{self._log_level}>\n"
            f"Config::Report Dir <{self._report_dir}>\n"
            f"Config::Workers <{self._workers}>\n"
            f"Config::Stop On Conflict <{self._stop_on_conflict}>\n"
            f"Config::Continue On Error <{self._continue_on_error}>\n"
            f"Config::Sort <{self._sort}>\n"
            f"Config::Genres <{genres_str}>"
        )

    # ------------------------------------------------------------------
    # Directory setters
    # ------------------------------------------------------------------
    def setDirectorySource(self, path: str) -> None:
        path = str(path or "").strip()
        if not path:
            raise ValueError("Source directory path cannot be empty.")
        self._directory_raw = path

    def setDirectoryTemp(self, path: str) -> None:
        path = str(path or "").strip()
        if not path:
            raise ValueError("Temp directory path cannot be empty.")
        self._directory_temp = path

    def setDirectoryTarget(self, path: str) -> None:
        path = str(path or "").strip()
        if not path:
            raise ValueError("Target directory path cannot be empty.")
        self._directory_vose = path

    # ------------------------------------------------------------------
    # Genre setters/getters
    # ------------------------------------------------------------------
    def setGenres(self, genres: Union[Iterable[GenresEnum], EnumMeta]) -> None:
        """
        Accepts either:
        - the enum class itself: GenresEnum
        - an iterable of enum members: [GenresEnum.ACTION, ...]
        """
        if isinstance(genres, EnumMeta):
            if genres is not GenresEnum:
                raise ValueError("Genres enum class must be GenresEnum.")
            self._genres = list(GenresEnum)
            return

        if genres is None:
            raise ValueError("Genres cannot be None.")

        parsed = list(genres)
        if not parsed:
            raise ValueError("Genres must be a non-empty iterable of GenresEnum values.")

        if not all(isinstance(genre, GenresEnum) for genre in parsed):
            raise ValueError("Genres must contain only GenresEnum values.")

        self._genres = parsed

    def getGenres(self) -> List[str]:
        return [genre.name for genre in self._genres]

    # ------------------------------------------------------------------
    # Directory getters
    # ------------------------------------------------------------------
    def getDirectorySource(self) -> str:
        return self._directory_raw

    def getDirectoryTemp(self) -> str:
        return self._directory_temp

    def getDirectoryTarget(self) -> str:
        return self._directory_vose

    # ------------------------------------------------------------------
    # Boolean flags
    # ------------------------------------------------------------------
    def is_dry_run(self) -> bool:
        return self._dry_run

    def set_dry_run(self, val: bool) -> None:
        self._dry_run = self._to_bool(val)

    def is_preflight(self) -> bool:
        return self._preflight

    def set_preflight(self, val: bool) -> None:
        self._preflight = self._to_bool(val)

    def is_plan(self) -> bool:
        return self._plan

    def set_plan(self, val: bool) -> None:
        self._plan = self._to_bool(val)

    def is_resume(self) -> bool:
        return self._resume

    def set_resume(self, val: bool) -> None:
        self._resume = self._to_bool(val)

    def get_stop_on_conflict(self) -> bool:
        return self._stop_on_conflict

    def set_stop_on_conflict(self, val: bool) -> None:
        self._stop_on_conflict = self._to_bool(val)
        if self._stop_on_conflict:
            self._continue_on_error = False

    def get_continue_on_error(self) -> bool:
        return self._continue_on_error

    def set_continue_on_error(self, val: bool) -> None:
        self._continue_on_error = self._to_bool(val)
        if self._continue_on_error:
            self._stop_on_conflict = False

    # ------------------------------------------------------------------
    # Numeric / text runtime options
    # ------------------------------------------------------------------
    def get_limit(self) -> int:
        return self._limit

    def set_limit(self, val: int) -> None:
        self._limit = self._to_non_negative_int(val, "limit")

    def get_log_level(self) -> str:
        return self._log_level

    def set_log_level(self, val: str) -> None:
        level = str(val or "").upper().strip()
        if level not in self.VALID_LOG_LEVELS:
            raise ValueError(f"log_level must be one of: {', '.join(sorted(self.VALID_LOG_LEVELS))}")
        self._log_level = level

    def get_report_dir(self) -> str:
        return self._report_dir

    def set_report_dir(self, val: str) -> None:
        report_dir = str(val or "").strip()
        if not report_dir:
            raise ValueError("report_dir cannot be empty.")
        self._report_dir = report_dir

    def get_workers(self) -> int:
        return self._workers

    def set_workers(self, val: int) -> None:
        self._workers = self._to_positive_int(val, "workers")

    def get_sort(self) -> str:
        return self._sort

    def set_sort(self, val: str) -> None:
        sort_mode = str(val or "").lower().strip()
        if sort_mode not in self.VALID_SORT_MODES:
            raise ValueError(f"sort must be one of: {', '.join(sorted(self.VALID_SORT_MODES))}")
        self._sort = sort_mode

    # Compatibility alias used by some callers
    def get_sort_mode(self) -> str:
        return self.get_sort()

    def set_sort_mode(self, val: str) -> None:
        self.set_sort(val)