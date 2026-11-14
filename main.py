"""CLI composition root for the organization and inventory use cases."""

import argparse
import logging
from contextlib import nullcontext
from pathlib import Path

from config.GenresConfig import GenresEnum
from src.adapters.exports import write_csv, write_report, write_text
from src.adapters.paths import (
    aliases,
    contains,
    library_path,
    output_path,
    validate_roots,
)
from src.domain.classes.ConfigClass import Config
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS
from src.domain.classes.FileSystemSynologyOSClass import FileSystemSynologyOS
from src.domain.classes.FileSystemWindowsClass import FileSystemWindows
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault
from src.domain.classes.Inventory import Inventory
from src.domain.classes.LibraryNames import name_key
from src.domain.classes.MovieManagerClass import MovieManager

BASE_DIR = Path(__file__).resolve().parent
FILESYSTEMS = {
    "windows": FileSystemWindows,
    "mac": FileSystemMacOS,
    "synology": FileSystemSynologyOS,
}
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or organize a Plex library, or export a read-only inventory."
    )
    config = parser.add_mutually_exclusive_group()
    config.add_argument("--config", help="Path to a local JSON configuration")
    config.add_argument(
        "--sandbox",
        action="store_true",
        help="Use only this repository's __sandbox__ fixture",
    )
    parser.add_argument(
        "--os",
        choices=FILESYSTEMS,
        default="windows",
        help="Filesystem adapter (default: windows)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply", action="store_true", help="Allow actual moves after validation"
    )
    mode.add_argument(
        "--dry-run",
        "--plan",
        dest="dry_run",
        action="store_true",
        help="Plan all stages (default)",
    )
    mode.add_argument(
        "--preflight", action="store_true", help="Validate the configured roots only"
    )
    mode.add_argument(
        "--inventory",
        action="store_true",
        help="List local videos without organizing the library",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New .csv or .txt file for --inventory, outside the library",
    )
    report = parser.add_mutually_exclusive_group()
    report.add_argument(
        "--report", type=Path, help="New JSON file for the plan or run results"
    )
    report.add_argument(
        "--report-dir", type=Path, help="Existing directory for a generated JSON report"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Include movies already in TEMP in the plan or run",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit new tagged RAW folders (0 means no limit)"
    )
    parser.add_argument(
        "--sort",
        choices=["name", "date"],
        help="Order new RAW folders by name or newest first",
    )
    parser.add_argument(
        "--stop-on-conflict",
        action="store_true",
        default=None,
        help="Abort apply on a conflict",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=None,
        help="Continue independent movies after errors",
    )
    parser.add_argument(
        "--workers",
        type=int,
        choices=[1],
        help="Moves are serialized; only 1 worker is supported",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console logging level",
    )
    return parser


def _read_config(args) -> Config:
    path = args.config or BASE_DIR / "config" / (
        "config.sandbox.json" if args.sandbox else "config.json"
    )
    config = Config(str(Path(path).expanduser()))
    for option in (
        "limit",
        "sort",
        "stop_on_conflict",
        "continue_on_error",
        "workers",
        "log_level",
    ):
        value = getattr(args, option)
        if value is not None:
            getattr(config, f"set_{option}")(value)
    return config


def _roots(
    config: Config, *, sandbox: bool, inventory: bool
) -> tuple[dict[str, Path], dict[str, Path]]:
    values = {
        "RAW": config.getDirectorySource(),
        "TEMP": config.getDirectoryTemp(),
        "VOSE": config.getDirectoryTarget(),
        **config.inventory_roots,
    }
    if sandbox:
        expected = {"RAW": "__RAW__", "TEMP": "__TMM_TEMP__", "VOSE": "__VOSE__"}
        if config.inventory_roots or any(
            values[label] != f"__sandbox__/{name}" for label, name in expected.items()
        ):
            raise ValueError(
                "Sandbox configuration must point only to the repository fixture"
            )
        values = {label: str(BASE_DIR / value) for label, value in values.items()}
    if not values["TEMP"] and values["RAW"]:
        values["TEMP"] = str(library_path(values["RAW"]).with_name("__TMM_TEMP__"))
    if not inventory and (not values["RAW"] or not values["VOSE"]):
        raise ValueError(
            "Configure directory_raw and directory_vose in a local JSON file"
        )
    all_roots = {label: library_path(value) for label, value in values.items() if value}
    if sandbox and not all(
        contains(BASE_DIR / "__sandbox__", root) for root in all_roots.values()
    ):
        raise ValueError("Sandbox root escaped the repository fixture")
    scan_roots = {label: path for label, path in all_roots.items() if label != "TEMP"}
    if any(aliases(root, BASE_DIR) for root in all_roots.values()):
        raise ValueError("A library root cannot contain the application checkout")
    if not scan_roots:
        raise ValueError("No library roots configured")
    validate_roots(all_roots, optional={"TEMP"})
    return all_roots, scan_roots


def _report_path(args, config: Config, roots: dict[str, Path]) -> Path | None:
    from uuid import uuid4

    if args.report:
        return output_path(args.report, roots.values())
    directory = args.report_dir
    if directory is None and config.get_report_dir() != "reports":
        directory = config.get_report_dir()
    if directory is not None:
        return output_path(
            Path(directory) / f"movie-run-{uuid4().hex}.json", roots.values()
        )
    return None


def _organize(args, config, fs, roots) -> int:
    if config.get_workers() != 1:
        raise ValueError("Only one worker is supported")
    if args.apply and (
        config.is_dry_run() or config.is_plan() or config.is_preflight()
    ):
        raise ValueError(
            "Apply is disabled by dry_run, plan or preflight in this configuration"
        )
    report = _report_path(args, config, roots)
    if report is not None and (report.exists() or not report.parent.is_dir()):
        raise ValueError(
            f"Report requires a new file in an existing directory: {report}"
        )
    config.set_dry_run(not args.apply)
    config.setGenres(GenresEnum)
    for label, setter in (
        ("RAW", config.setDirectorySource),
        ("TEMP", config.setDirectoryTemp),
        ("VOSE", config.setDirectoryTarget),
    ):
        setter(str(roots[label]))
    fs.setConfig(config)
    filters = FilterServiceDefault()
    filters.setGenres(config.getGenres())
    manager = MovieManager()
    manager.setServiceConfig(config)
    manager.setServiceFileSystem(fs)
    manager.setServiceFilter(filters)

    with fs.lock(roots["RAW"]):
        run = manager.start(recover=args.resume, apply=args.apply)
        logger.info(
            "Mode: %s | roots: %s | before execution: %s",
            run.mode,
            run.roots,
            run.counts(),
        )
        for step in run.issues:
            logger.warning(
                "%s: %s -> %s (%s)",
                step.status,
                step.source,
                step.destination,
                step.reason,
            )
        if not args.apply:
            for job in run.jobs:
                for step in job:
                    logger.info(
                        "Planned %s: %s -> %s",
                        step.stage,
                        step.source,
                        step.destination,
                    )
        report_stream = (
            output_path(report, roots.values()).open("x", encoding="utf-8")
            if report
            else nullcontext(None)
        )
        with report_stream as stream:
            try:
                if (
                    not any(step.status == "error" for step in run.issues)
                    or config.get_continue_on_error()
                ):
                    manager.execute(run)
            finally:
                if stream is not None:
                    write_report(stream, run)
    if report:
        logger.info("Report: %s", report)
    counts = run.counts()
    logger.info("Result: %s", counts)
    if counts.get("error"):
        return 1
    return 2 if counts.get("conflict") or counts.get("pending") else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.inventory != bool(args.output):
        parser.error("--inventory and --output must be used together")
    if args.inventory and (
        args.report or args.report_dir or args.resume or args.limit is not None
    ):
        parser.error(
            "--inventory does not use --report, --report-dir, --resume or --limit"
        )
    try:
        config = _read_config(args)
        logging.basicConfig(
            level=args.log_level or config.get_log_level(),
            format="%(levelname)s: %(message)s",
        )
        roots, scan_roots = _roots(
            config, sandbox=args.sandbox, inventory=args.inventory
        )
        fs = FILESYSTEMS[args.os](
            apply=args.apply,
            roots=tuple(roots[key] for key in ("RAW", "TEMP", "VOSE") if key in roots),
        )
        if args.inventory:
            suffix = args.output.suffix.lower()
            if suffix not in {".csv", ".txt"}:
                raise ValueError("Inventory output must end in .csv or .txt")
            path = output_path(args.output, roots.values())
            if path.exists() or not path.parent.is_dir():
                raise ValueError(
                    f"Inventory requires a new file in an existing directory: {path}"
                )
            genres = {name_key(genre.name): genre.value for genre in GenresEnum}
            records = Inventory(fs, genres).scan(scan_roots)
            encoding = "utf-8-sig" if suffix == ".csv" else "utf-8"
            with output_path(path, roots.values()).open(
                "x", encoding=encoding, newline=""
            ) as stream:
                (write_csv if suffix == ".csv" else write_text)(stream, records)
            print(f"{len(records)} video record(s): {path}")
            return 0
        if args.preflight or (config.is_preflight() and not args.apply):
            for label, path in roots.items():
                print(f"{label}: {path}")
            return 0
        return _organize(args, config, fs, roots)
    except (OSError, ValueError) as exc:
        logger.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logger.error(
            "Interrupted. Inspect RAW, TEMP, VOSE and the report before retrying."
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
