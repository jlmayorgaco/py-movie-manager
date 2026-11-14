"""Plan and execute the RAW -> TEMP -> VOSE use case through filesystem ports."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.domain.classes.LibraryNames import (
    TRANSFER_PREFIX,
    VIDEO_SUFFIXES,
    movie_entry_issue,
    name_key,
    reserved,
    staging_name,
    valid_movie_name,
)
from src.domain.interfaces.IFilterServiceInterface import IFilterService
from src.domain.interfaces.IMovieManagerInterface import IMovieManager
from src.domain.interfaces.LibraryFileSystem import Entry, LibraryFileSystem

logger = logging.getLogger(__name__)


@dataclass
class Step:
    stage: str
    source: Path
    destination: Path | None
    parents: tuple[Path, ...] = ()
    status: str = "planned"
    reason: str = ""
    genre_tag: str | None = None
    suggested_genres: tuple[str, ...] = ()


@dataclass
class Run:
    mode: str
    roots: dict[str, Path]
    jobs: list[list[Step]] = field(default_factory=list)
    issues: list[Step] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return dict(Counter(step.status for step in self.steps()))

    def steps(self):
        yield from self.issues
        for job in self.jobs:
            yield from job

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "roots": self.roots,
            "counts": self.counts(),
            "operations": [asdict(step) for step in self.steps()],
        }


class MovieManager(IMovieManager):
    """Keep the existing service wiring; plan from disk and execute per movie."""

    def __init__(self) -> None:
        self.configService = None
        self.fileSystemService: LibraryFileSystem | None = None
        self.filterService: IFilterService | None = None
        self.scrapperService = None
        self._entries: dict[Path, dict[str, list[Entry]]] = {}
        self._reserved_targets: dict[tuple[str, ...], tuple[Path, Path]] = {}
        self._blocked: set[Path] = set()
        self._cleaned: dict[Path, dict[str, Entry]] = {}

    def setServiceConfig(self, config) -> None:
        self.configService = config

    def setServiceFileSystem(self, filesystem: LibraryFileSystem) -> None:
        self.fileSystemService = filesystem

    def setServiceFilter(self, service: IFilterService) -> None:
        self.filterService = service

    def setServiceScrapper(self, service) -> None:
        # Retained for compatibility; local genre tags are sufficient.
        self.scrapperService = service

    def start(self, *, recover: bool = False, apply: bool = False) -> Run:
        """Build the complete plan without mutating the filesystem."""
        config, fs = self.configService, self.fileSystemService
        if config is None or fs is None or self.filterService is None:
            raise ValueError(
                "Configuration, filesystem and filter services are required"
            )
        roots = {
            "RAW": Path(config.getDirectorySource()),
            "TEMP": Path(config.getDirectoryTemp()),
            "VOSE": Path(config.getDirectoryTarget()),
        }
        run = Run("apply" if apply and not config.is_dry_run() else "dry-run", roots)
        self._entries.clear()
        self._reserved_targets.clear()
        self._blocked.clear()
        self._cleaned.clear()
        self._plan_temp(run, recover)

        candidates = []
        for entry in fs.entries(roots["RAW"]):
            if reserved(entry.path.name):
                continue
            if entry.kind == "directory":
                genre = self.filterService.genre_tag(entry.path.name)
                if genre is None:
                    self._issue(
                        run, entry.path, entry.path, "missing_genre_tag", "skipped"
                    )
                elif (canonical := self.filterService.resolve_genre(genre)) is not None:
                    candidates.append((entry, canonical))
                else:
                    self._unknown_genre(run, entry.path, genre)
            elif entry.kind == "link":
                self._issue(run, entry.path, entry.path, "link_not_followed", "skipped")
            elif entry.kind == "file" and entry.path.suffix.lower() in VIDEO_SUFFIXES:
                self._issue(run, entry.path, entry.path, "loose_raw_video", "skipped")

        if config.get_sort() == "date":
            candidates.sort(key=lambda candidate: -candidate[0].modified_ns)
        limit = config.get_limit()
        for entry, genre in candidates[: limit or None]:
            try:
                self._plan_movie(run, entry.path, genre, from_raw=True)
            except (OSError, ValueError) as exc:
                self._issue(run, entry.path, entry.path, str(exc), "error")
        run.jobs = [job for job in run.jobs if job[0].source not in self._blocked]
        return run

    def _children(self, path: Path) -> dict[str, list[Entry]]:
        if path not in self._entries:
            indexed: dict[str, list[Entry]] = {}
            parent = self.fileSystemService.entry(path)
            if parent is not None:
                if parent.kind != "directory":
                    raise ValueError(f"Expected a real directory: {path}")
                for entry in self.fileSystemService.entries(path):
                    indexed.setdefault(name_key(entry.path.name), []).append(entry)
            self._entries[path] = indexed
        return self._entries[path]

    def _matches(self, path: Path) -> list[Entry]:
        return self._children(path.parent).get(name_key(path.name), [])

    def _cleaned_matches(self, path: Path) -> dict[str, Entry]:
        if path not in self._cleaned:
            self._cleaned[path] = {
                name_key(self.filterService.clean_folder_name(entry.path.name)): entry
                for entries in self._children(path).values()
                for entry in entries
            }
        return self._cleaned[path]

    def _genre_path(self, root: Path, genre: str) -> Path:
        path = root / genre
        matches = self._matches(path)
        if matches:
            if len(matches) != 1 or matches[0].kind != "directory":
                raise ValueError(f"Ambiguous or unsafe genre directory: {path}")
            return matches[0].path
        return path

    def _plan_temp(self, run: Run, recover: bool) -> None:
        configured = {
            name_key(genre): genre for genre in self.configService.getGenres()
        }
        for group in self._children(run.roots["TEMP"]).values():
            for entry in group:
                if reserved(entry.path.name) and not name_key(
                    entry.path.name
                ).startswith(TRANSFER_PREFIX):
                    continue
                genre = configured.get(name_key(entry.path.name))
                if entry.kind != "directory" or not genre or len(group) != 1:
                    self._issue(run, entry.path, entry.path, "unrecognized_temp_entry")
                    continue
                for movies in self._children(entry.path).values():
                    for movie in movies:
                        source = movie.path
                        if reserved(source.name) and not name_key(
                            source.name
                        ).startswith(TRANSFER_PREFIX):
                            continue
                        if (
                            movie.kind != "directory"
                            or len(movies) != 1
                            or reserved(source.name)
                        ):
                            self._issue(run, source, source, "unrecognized_temp_entry")
                            continue
                        tag = self.filterService.genre_tag(source.name)
                        if tag is not None:
                            canonical = self.filterService.resolve_genre(tag)
                            if canonical is None:
                                self._unknown_genre(run, source, tag)
                                continue
                            if canonical != genre:
                                self._issue(run, source, source, "temp_genre_mismatch")
                                continue
                        if not recover:
                            clean = self.filterService.clean_folder_name(source.name)
                            self._issue(
                                run,
                                source,
                                run.roots["VOSE"] / genre / clean,
                                "pending_temp_use_resume",
                                "pending",
                            )
                        else:
                            try:
                                self._plan_movie(run, source, genre, from_raw=False)
                            except (ValueError, OSError) as exc:
                                self._issue(run, source, source, str(exc), "error")

    @staticmethod
    def _key(path: Path) -> tuple[str, ...]:
        return tuple(map(name_key, path.parts))

    @staticmethod
    def _issue(
        run: Run,
        source: Path,
        destination: Path,
        reason: str,
        status: str = "conflict",
        stage: str = "review",
    ) -> None:
        run.issues.append(
            Step(stage, source, destination, status=status, reason=reason)
        )

    def _unknown_genre(self, run: Run, source: Path, tag: str) -> None:
        run.issues.append(
            Step(
                "review",
                source,
                None,
                status="conflict",
                reason="unknown_genre_tag",
                genre_tag=tag,
                suggested_genres=self.filterService.suggest_genres(tag),
            )
        )

    def _plan_movie(
        self, run: Run, source: Path, genre: str, *, from_raw: bool
    ) -> None:
        fs = self.fileSystemService
        clean = self.filterService.clean_folder_name(source.name)
        if not valid_movie_name(clean, windows=bool(source.drive)):
            self._issue(run, source, source, "invalid_clean_name")
            return
        temp, vose = run.roots["TEMP"], run.roots["VOSE"]
        temp_genre = self._genre_path(temp, genre) if from_raw else source.parent
        clean_temp = temp_genre / clean
        final_genre = self._genre_path(vose, genre)
        final = final_genre / clean

        try:
            tree = fs.tree(source)
        except ValueError as exc:
            self._issue(run, source, final, str(exc))
            return
        for relative, entry in tree.items():
            reason = movie_entry_issue(
                entry.path.name,
                allow_synology_metadata=bool(relative.parts)
                and entry.kind == "directory",
            )
            if reason:
                self._issue(run, source, final, reason)
                return
        if not any(entry.kind == "file" for entry in tree.values()):
            self._issue(run, source, final, "empty_directory", "skipped")
            return

        staged = temp_genre / source.name if from_raw else source
        final_matches = self._matches(final)
        if final_matches:
            for existing in final_matches:
                reason = (
                    self._classify(tree, existing)
                    if len(final_matches) == 1
                    else "ambiguous_destination"
                )
                self._issue(run, source, existing.path, reason)
            return

        if from_raw:
            # Include older TEMP folders whose tags have yet to be removed.
            matching = self._matches(staged)
            existing = (
                matching[0]
                if matching
                else self._cleaned_matches(temp_genre).get(name_key(clean))
            )
            if existing is not None:
                self._issue(run, source, existing.path, "matching_temp_entry")
                return
        elif staged != clean_temp:
            for existing in self._matches(clean_temp):
                if existing.path != source:
                    self._issue(run, source, existing.path, "temp_rename_collision")
                    return

        for target in dict.fromkeys((final, clean_temp, staged)):
            staging = target.with_name(staging_name(target.name))
            if self._matches(staging):
                self._issue(
                    run, source, staging, "interrupted_transfer_staging_needs_review"
                )
                return

        for target in dict.fromkeys((final, clean_temp, staged)):
            key = self._key(target)
            other = self._reserved_targets.setdefault(key, (source, target))
            if other[0] != source:
                self._issue(
                    run,
                    source,
                    target,
                    f"planned_destination_collision_with: {other[0]}",
                )
                if other[0] not in self._blocked:
                    self._issue(
                        run,
                        other[0],
                        other[1],
                        f"planned_destination_collision_with: {source}",
                    )
                self._blocked.update((source, other[0]))

        steps = []
        if from_raw:
            steps.append(Step("raw_to_temp", source, staged, (temp, temp_genre)))
        if staged != clean_temp:
            steps.append(Step("rename_in_temp", staged, clean_temp))
        steps.append(Step("temp_to_vose", clean_temp, final, (final_genre,)))
        run.jobs.append(steps)

    def _classify(self, source: dict[Path, Entry], destination: Entry) -> str:
        """Classify an occupied destination without moving or deleting either copy."""
        if destination.kind != "directory":
            return f"destination_is_{destination.kind}"
        fs = self.fileSystemService
        try:
            target = fs.tree(destination.path)
        except ValueError:
            return "unsafe_entry_inside_destination"
        common = source.keys() & target.keys()
        if any(source[key].kind != target[key].kind for key in common):
            return "file_directory_collision"
        if any(
            source[key].kind == "file" and not fs.same_content(source[key], target[key])
            for key in sorted(common)
        ):
            return "same_name_different_content"
        if source.keys() == target.keys():
            return "identical_tree_preserved"
        if source.keys() < target.keys():
            return "destination_has_additional_entries"
        if target.keys() < source.keys():
            return "destination_missing_entries_possible_partial_transfer"
        return "different_releases_or_companion_files"

    def execute(self, run: Run) -> None:
        config, fs = self.configService, self.fileSystemService
        if run.mode != "apply" or config.is_dry_run():
            return
        if config.get_stop_on_conflict() and any(
            issue.status == "conflict" for issue in run.issues
        ):
            return
        created: set[Path] = set()
        for job in run.jobs:
            for step in job:
                assert step.destination is not None
                step.status = "in_progress"
                logger.info("%s: %s -> %s", step.stage, step.source, step.destination)
                try:
                    for parent in step.parents:
                        if parent not in created:
                            fs.make_directory(parent)
                            created.add(parent)
                    fs.transfer(step.source, step.destination)
                except (OSError, ValueError) as exc:
                    step.status = (
                        "conflict" if isinstance(exc, FileExistsError) else "error"
                    )
                    step.reason = str(exc)
                    logger.warning("%s: %s", step.status, step.reason)
                    if (
                        step.status == "conflict" and config.get_stop_on_conflict()
                    ) or (
                        step.status == "error" and not config.get_continue_on_error()
                    ):
                        return
                    break
                else:
                    step.status = "completed"
