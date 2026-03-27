## ------------------------------------------------------------------------------ ##
## ---- PyMovieManager ---------------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
"""
PyMovieManager: A Python-based tool for organizing and managing movie files
for use with a Plex Media Server. This script orchestrates the initialization
and execution of core services required to identify, filter, and move movies
into genre-based folders.

Author: Jorge Luis Mayorga Taborda (jlmayorgaco)
Date: January 20, 2025
Version: 1.0.3
License: MIT License
GitHub: https://github.com/jlmayorgaco/py-movie-manager
Dependencies: See requirements.txt or pyproject.toml.
"""

## ------------------------------------------------------------------------------ ##
## ---- PyMovieManager CLI Loader ---------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
import os
import sys
import time
import logging
import argparse
from typing import Any, Iterable, Optional

from dotenv import load_dotenv

from config.GenresConfig import GenresEnum
from src.domain.classes.ConfigClass import Config
from src.domain.classes.ScrapperServiceIMDB import ScrapperServiceIMDB
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault
from src.domain.classes.FileSystemWindowsClass import FileSystemWindows
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS
from src.domain.classes.FileSystemSynologyOSClass import FileSystemSynologyOS
from src.domain.classes.MovieManagerClass import MovieManager
from src.domain.classes.RunSummaryClass import RunSummary

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


## ------------------------------------------------------------------------------ ##
## ---- Logging Helpers -------------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
class ExcludeLoggerPrefixFilter(logging.Filter):
    """
    Exclude noisy logger prefixes from console output while keeping them in file logs.
    """

    def __init__(self, excluded_prefixes: list[str]):
        super().__init__()
        self.excluded_prefixes = excluded_prefixes

    def filter(self, record: logging.LogRecord) -> bool:
        return not any(record.name.startswith(prefix) for prefix in self.excluded_prefixes)


def _resolve_path(path: Optional[str]) -> Optional[str]:
    """Resolve a path relative to the repository root."""
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(BASE_DIR, path))


def configure_logging(log_level: str = "INFO", report_dir: Optional[str] = None) -> tuple[str, str]:
    """
    Configure logging with:
    - concise console logging
    - detailed file logging
    Returns:
        run_id, log_path
    """
    resolved_report_dir = _resolve_path(report_dir) or os.path.join(BASE_DIR, "reports")
    logs_dir = os.path.join(resolved_report_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    run_id = time.strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(logs_dir, f"run_{run_id}.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear previous handlers to avoid duplicated logs
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Console handler: concise, less noisy
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    console_handler.addFilter(
        ExcludeLoggerPrefixFilter(
            excluded_prefixes=[
                "src.domain.classes.FilterServiceDefaultClass",
            ]
        )
    )

    # File handler: detailed for audit/debug
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return run_id, log_path


def log_header(title: str) -> None:
    logger.info("")
    logger.info("=" * 78)
    logger.info(title)
    logger.info("=" * 78)


## ------------------------------------------------------------------------------ ##
## ---- Config Helpers --------------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
def _apply_config_override(
    config_obj: Config,
    value: Any,
    setter_names: Iterable[str],
    *,
    preprocess=None,
) -> None:
    """
    Apply a CLI override to Config using the first available setter name.
    This avoids crashing if ConfigClass evolved and setter names changed.
    """
    if value is None:
        return

    if preprocess is not None:
        value = preprocess(value)

    for setter_name in setter_names:
        setter = getattr(config_obj, setter_name, None)
        if callable(setter):
            setter(value)
            logger.debug("Applied config override via %s(%r)", setter_name, value)
            return

    logger.debug(
        "Could not apply config override %r. None of these setters exist: %s",
        value,
        ", ".join(setter_names),
    )


def _validate_windows_paths(config_obj: Config, os_type: str) -> None:
    """
    Fail fast if Windows mode is used with Synology/Linux internal paths.
    """
    if os_type != "windows":
        return

    raw_path = config_obj.getDirectorySource()
    temp_path = config_obj.getDirectoryTemp()
    vose_path = config_obj.getDirectoryTarget()

    for label, path in (
        ("directory_raw", raw_path),
        ("directory_temp", temp_path),
        ("directory_vose", vose_path),
    ):
        if path and str(path).startswith("/"):
            raise ValueError(
                f"Invalid Windows path in {label}: '{path}'. "
                "Use a mapped drive like Z:\\... or a UNC path like \\\\NAS\\share\\..."
            )


def _resolve_config_file(args: argparse.Namespace) -> str:
    if args.config:
        return _resolve_path(args.config) or ""

    default_config = "config/config.sandbox.json" if args.sandbox else "config/config.json"
    return _resolve_path(default_config) or ""


def _effective_report_dir(args: argparse.Namespace) -> str:
    return _resolve_path(args.report_dir) or os.path.join(BASE_DIR, "reports")


## ------------------------------------------------------------------------------ ##
## ---- Initialize Services ---------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
def initialize_movie_manager_services(args: argparse.Namespace, config_path: str) -> MovieManager:
    """Initialize and configure all services required by MovieManager."""
    try:
        cnfg = Config(config_path)
        cnfg.setGenres(GenresEnum)

        # CLI overrides (safe / backwards-compatible)
        _apply_config_override(cnfg, args.dry_run, ("set_dry_run",))
        _apply_config_override(cnfg, args.preflight, ("set_preflight",))
        _apply_config_override(cnfg, args.plan, ("set_plan",))
        _apply_config_override(cnfg, args.resume, ("set_resume",))
        _apply_config_override(cnfg, args.stop_on_conflict, ("set_stop_on_conflict",))
        _apply_config_override(cnfg, args.continue_on_error, ("set_continue_on_error",))
        _apply_config_override(cnfg, args.limit, ("set_limit",))
        _apply_config_override(cnfg, args.log_level, ("set_log_level",))
        _apply_config_override(
            cnfg,
            args.report_dir,
            ("set_report_dir",),
            preprocess=_resolve_path,
        )
        _apply_config_override(cnfg, args.workers, ("set_workers",))
        _apply_config_override(cnfg, args.sort, ("set_sort", "set_sort_mode"))

        _validate_windows_paths(cnfg, args.os)

        log_header("CONFIGURATION")
        logger.info("Config file     : %s", config_path)
        logger.info("OS mode         : %s", args.os)
        logger.info("RAW             : %s", cnfg.getDirectorySource())
        logger.info("TEMP            : %s", cnfg.getDirectoryTemp())
        logger.info("VOSE            : %s", cnfg.getDirectoryTarget())
        logger.info("Dry run         : %s", cnfg.is_dry_run())

        report_dir_getter = getattr(cnfg, "get_report_dir", None)
        if callable(report_dir_getter):
            logger.info("Report dir      : %s", report_dir_getter())

        limit_getter = getattr(cnfg, "get_limit", None)
        if callable(limit_getter):
            logger.info("Limit           : %s", limit_getter())

        continue_on_error_getter = getattr(cnfg, "get_continue_on_error", None)
        if callable(continue_on_error_getter):
            logger.info("Continue error  : %s", continue_on_error_getter())

        # Scrapper Service
        imdb = ScrapperServiceIMDB()
        imdb.setApiKey(os.getenv("IMDB_API_KEY", "default_api_key"))
        logger.info("IMDb service    : initialized")

        # Filter Service
        filter_service = FilterServiceDefault()
        filter_service.setGenres(cnfg.getGenres())
        filter_service.setGenreSearchTag(os.getenv("GENRE_TAG", "[g-*]"))
        filter_service.setDirectorSearchTag(os.getenv("DIRECTOR_TAG", "[d-*]"))
        logger.info("Filter service  : initialized")

        # File System Service
        os_type = args.os
        if os_type == "windows":
            file_system = FileSystemWindows()
        elif os_type == "synology":
            file_system = FileSystemSynologyOS()
        elif os_type == "mac":
            file_system = FileSystemMacOS()
        else:
            raise ValueError(f"Unsupported OS: {os_type}")

        file_system.setConfig(cnfg)
        file_system.setFilter(filter_service)
        logger.info("Filesystem      : %s", os_type)

        # Movie Manager
        movie_manager = MovieManager()
        movie_manager.setServiceConfig(cnfg)
        movie_manager.setServiceFilter(filter_service)
        movie_manager.setServiceFileSystem(file_system)
        movie_manager.setServiceScrapper(imdb)
        logger.info("MovieManager    : initialized")

        return movie_manager

    except Exception as exc:
        logger.exception("Initialization error: %s", exc)
        raise


## ------------------------------------------------------------------------------ ##
## ---- Workflow Runner -------------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
def run_movie_manager(movie_manager: MovieManager) -> None:
    """Execute the main workflow for movie management."""
    try:
        log_header("WORKFLOW START")
        logger.info("Dry run mode    : %s", movie_manager.configService.is_dry_run())

        is_preflight = getattr(movie_manager.configService, "is_preflight", None)
        if callable(is_preflight) and is_preflight():
            logger.info("Mode            : PREFLIGHT")
            movie_manager.preflight()
            logger.info("Preflight completed")
            return

        is_plan = getattr(movie_manager.configService, "is_plan", None)
        if callable(is_plan) and is_plan():
            logger.info("Mode            : PLAN")
            movie_manager.plan()
            logger.info("Plan completed")
            return

        logger.info("Mode            : LIVE RUN")

        movie_manager.start()
        logger.info("Stage complete  : start")

        movie_manager.creating_temp_genres()
        logger.info("Stage complete  : creating_temp_genres")

        movie_manager.moving_to_temp()
        logger.info("Stage complete  : moving_to_temp")

        movie_manager.renaming_in_temp()
        logger.info("Stage complete  : renaming_in_temp")

        movie_manager.moving_to_vose()
        logger.info("Stage complete  : moving_to_vose")

        delete_temp = getattr(movie_manager, "deleting_temp", None)
        if callable(delete_temp):
            delete_temp()
            logger.info("Stage complete  : deleting_temp")

        log_header("WORKFLOW FINISHED")
        logger.info("Run completed successfully")

    except Exception as exc:
        logger.exception("Workflow error: %s", exc)
        raise

## ------------------------------------------------------------------------------ ##
## ---- CLI -------------------------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PyMovieManager Runner")

    parser.add_argument("--sandbox", action="store_true", help="Use sandbox config")

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a specific config JSON file",
    )

    parser.add_argument(
        "--os",
        choices=["windows", "mac", "synology"],
        default="windows",
        help="Operating system environment",
    )

    parser.add_argument("--preflight", action="store_true", help="Run preflight checks")
    parser.add_argument("--plan", action="store_true", help="Show proposed changes without execution")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifications")
    parser.add_argument("--resume", action="store_true", help="Resume from previous manifest")
    parser.add_argument("--limit", type=int, help="Limit the number of folders to process")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Configure log output level",
    )
    parser.add_argument("--report-dir", type=str, help="Directory to store run manifests and logs")
    parser.add_argument("--workers", type=int, help="Number of concurrent workers (default: 1)")
    parser.add_argument("--stop-on-conflict", action="store_true", help="Halt execution on first conflict")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing distinct folders even if one fails",
    )
    parser.add_argument("--sort", choices=["name", "date"], help="Sorting strategy for movie folders")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    console_level = args.log_level or "INFO"
    effective_report_dir = _effective_report_dir(args)
    run_id, log_path = configure_logging(console_level, effective_report_dir)

    logger.info("▶️ Run ID       : %s", run_id)
    logger.info("📝 Log file     : %s", log_path)

    config_file = _resolve_config_file(args)
    logger.info("▶️ Starting PyMovieManager [OS=%s] [Config=%s]", args.os, config_file)

    try:
        movie_manager = initialize_movie_manager_services(args, config_file)
        run_movie_manager(movie_manager)
    except Exception:
        logger.exception("Workflow error")
        raise