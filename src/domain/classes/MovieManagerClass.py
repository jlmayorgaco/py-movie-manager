import glob
import hashlib
import logging
import os
import time
from typing import Dict, Iterable, List, Tuple

from tqdm import tqdm

from src.domain.interfaces.IMovieManagerInterface import IMovieManager
from src.domain.classes.ConfigClass import Config
from src.domain.classes.RunManifestClass import RunManifest


class MovieManager(IMovieManager):
    """
    MovieManager: organize and move movie folders by genre.

    Safety behavior:
    - Uses a single TEMP path resolution strategy.
    - Respects dry_run inside MovieManager.
    - If destination movie folder already exists in VOSE during pre-check:
        * it is skipped safely (source untouched)
        * nothing is moved to TEMP
    - If destination movie folder exists during TEMP -> VOSE merge:
        * missing files are copied
        * identical files are NOT copied and are renamed in source as AlreadyCopied_<name>
        * if real conflicts exist, that movie is SKIPPED safely (source untouched)
    - Source folder is deleted only after verification succeeds.
    - TEMP is only deleted if there is no pending content left inside it.
    - dry_run does not mutate files and will refuse to process stale TEMP content.
    """

    TEMP_DIR_NAME = "__TMM_TEMP__"
    ALREADY_COPIED_PREFIX = "AlreadyCopied_"

    # SMB-friendly comparison strategy:
    # - small files: full SHA-256
    # - large files: compare size + first/last chunk hashes
    FULL_HASH_THRESHOLD = 32 * 1024 * 1024  # 32 MB
    SAMPLE_CHUNK_SIZE = 1024 * 1024  # 1 MB

    def __init__(self):
        self.configService = None
        self.scrapperService = None
        self.filterService = None
        self.fileSystemService = None
        self.run_manifest = None
        self.logger = logging.getLogger(__name__)
        self._dry_run_temp_is_dirty = False

    def __str__(self) -> str:
        return (
            f"MovieManager::ConfigService <{self.configService}>\n"
            f"MovieManager::ScrapperService <{self.scrapperService}>\n"
            f"MovieManager::FilterService <{self.filterService}>\n"
            f"MovieManager::FileSystemService <{self.fileSystemService}>"
        )

    # ------------------------------------------------------------------
    # Service wiring
    # ------------------------------------------------------------------
    def setServiceConfig(self, configService: Config) -> None:
        self.configService = configService

    def setServiceFilter(self, filterService) -> None:
        self.filterService = filterService

    def setServiceFileSystem(self, filesystemService) -> None:
        self.fileSystemService = filesystemService

    def setServiceScrapper(self, scrapperService) -> None:
        self.scrapperService = scrapperService

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def preflight(self) -> None:
        """Validate paths and report configuration without making changes."""
        self._validate_services()

        raw_path = self.configService.getDirectorySource()
        vose_path = self.configService.getDirectoryTarget()
        temp_path = self._get_temp_path(raw_path)

        raw_exists = self._path_exists(raw_path)
        vose_exists = self._path_exists(vose_path)
        temp_exists = self._path_exists(temp_path)

        self.logger.info("=== PREFLIGHT REPORT ===")
        self.logger.info("RAW  : %s (exists=%s)", raw_path, raw_exists)
        self.logger.info("VOSE : %s (exists=%s)", vose_path, vose_exists)
        self.logger.info("TEMP : %s (exists=%s)", temp_path, temp_exists)

        if not raw_exists:
            raise FileNotFoundError(f"Source RAW path does not exist: {raw_path}")

        if not vose_exists:
            raise FileNotFoundError(f"Destination VOSE path does not exist: {vose_path}")

        if temp_exists and self._temp_has_pending_content(temp_path):
            self.logger.warning("TEMP already contains pending content: %s", temp_path)

        self.logger.info("Preflight OK")

    def plan(self) -> None:
        """Scan RAW and show a useful summary without making changes."""
        self._validate_services()

        raw_path = self.configService.getDirectorySource()
        vose_path = self.configService.getDirectoryTarget()

        self.fileSystemService.cd(raw_path)
        folders = self.fileSystemService.get_folders()
        folders_filtered = sorted(self.filterService.filter_folders(folders))

        limit = self._get_limit()
        if limit and limit > 0:
            folders_filtered = folders_filtered[:limit]

        total = len(folders_filtered)
        unknown = 0
        exists_in_vose = 0
        will_move = 0
        preview_rows: List[str] = []

        for folder in folders_filtered:
            genre = self.filterService.getGenreByFolderName(folder)
            genre = self.filterService.getGenreByMostLikehood(genre)
            clean_name = self.filterService.clean_folder_name(folder)

            if not genre or genre == "Unknown":
                unknown += 1
                if len(preview_rows) < 20:
                    preview_rows.append(f"SKIP    | {folder} | no mapped genre")
                continue

            final_vose_path = self.fileSystemService.join(vose_path, genre, clean_name)
            if self._path_exists(final_vose_path):
                exists_in_vose += 1
                if len(preview_rows) < 20:
                    preview_rows.append(f"EXISTS  | {folder} -> {final_vose_path}")
            else:
                will_move += 1
                if len(preview_rows) < 20:
                    preview_rows.append(f"MOVE    | {folder} -> {final_vose_path}")

        self.logger.info("=== PLAN SUMMARY ===")
        self.logger.info("Total candidatos : %d", total)
        self.logger.info("Movería          : %d", will_move)
        self.logger.info("Ya existen       : %d", exists_in_vose)
        self.logger.info("Sin género       : %d", unknown)
        self.logger.info("---- Preview ----")
        for row in preview_rows:
            self.logger.info(row)
        self.logger.info("====================")

    def start(self) -> None:
        """Initialize workflow and prepare TEMP."""
        self._validate_services()

        raw_path = self.configService.getDirectorySource()
        temp_path = self._get_temp_path(raw_path)

        self.logger.info("Workflow start")
        self.logger.info("RAW  : %s", raw_path)
        self.logger.info("TEMP : %s", temp_path)

        report_dir = self._get_report_dir() or "reports"
        report_dir = os.path.abspath(report_dir)

        run_id = time.strftime("%Y%m%d_%H%M%S")
        self.run_manifest = RunManifest(report_dir, run_id)

        if self._is_resume():
            manifests = sorted(glob.glob(os.path.join(report_dir, "manifest_run_*.jsonl")))
            if manifests:
                latest = manifests[-1]
                self.logger.info("Resuming from manifest: %s", latest)
                self.run_manifest.load_existing(latest)
            else:
                self.logger.warning("Resume requested but no previous manifest found.")

        self.fileSystemService.cd(raw_path)
        self._prepare_temp_directory(temp_path)

        # Dry-run protection: do not simulate over stale TEMP data.
        if self._is_dry_run() and self._temp_has_pending_content(temp_path):
            self._dry_run_temp_is_dirty = True
            self.logger.warning(
                "DRY RUN detected pre-existing content inside TEMP. "
                "renaming_in_temp() and moving_to_vose() will be skipped to avoid a contaminated simulation: %s",
                temp_path,
            )

    def creating_temp_genres(self) -> None:
        """Create genre directories inside TEMP."""
        self._validate_services()

        temp_path = self._get_temp_path(self.configService.getDirectorySource())
        self.fileSystemService.ensure_directory_exists(temp_path)
        self.fileSystemService.cd(temp_path)

        genres = self.configService.getGenres()
        self.logger.info("Preparing TEMP genre directories: %d", len(genres))

        for genre in genres:
            try:
                self.fileSystemService.mkdir(genre)
            except OSError:
                self.logger.exception("Failed to create TEMP genre directory '%s'", genre)
                raise

        self.logger.info("TEMP genre directories ready")

    def moving_to_temp(self) -> None:
        """
        Move movie folders from RAW to TEMP/<GENRE>/<CLEAN_NAME>.

        Safety-first pre-check:
        - If the final destination already exists in VOSE, skip safely and leave RAW untouched.
        """
        self._validate_services()

        raw_path = self.configService.getDirectorySource()
        vose_path = self.configService.getDirectoryTarget()
        temp_path = self._get_temp_path(raw_path)

        self.fileSystemService.cd(raw_path)
        folders = self.fileSystemService.get_folders()
        folders_filtered = sorted(self.filterService.filter_folders(folders))

        limit = self._get_limit()
        if limit and limit > 0:
            folders_filtered = folders_filtered[:limit]
            self.logger.info("Limit applied: %d folders", len(folders_filtered))

        total_folders = len(folders_filtered)
        counters = {"ok": 0, "skip": 0, "exists": 0, "conflict": 0, "error": 0}
        started_at = time.time()

        self.logger.info("RAW->TEMP candidates: %d", total_folders)

        with tqdm(total=total_folders, desc="RAW -> TEMP", unit="folder") as pbar:
            for index, folder in enumerate(folders_filtered, start=1):
                genre_from_folder = self.filterService.getGenreByFolderName(folder)
                most_likely_genre = self.filterService.getGenreByMostLikehood(genre_from_folder)

                if not most_likely_genre or most_likely_genre == "Unknown":
                    counters["skip"] += 1
                    self._record_state(folder, "skipped_unknown_genre")
                    self._log_stage_progress(
                        stage="RAW->TEMP",
                        current=index,
                        total=total_folders,
                        started_at=started_at,
                        current_name=folder,
                        counters=counters,
                    )
                    pbar.update(1)
                    continue

                clean_name = self.filterService.clean_folder_name(folder)
                from_path = self.fileSystemService.join(raw_path, folder)
                to_temp_path = self.fileSystemService.join(temp_path, most_likely_genre, clean_name)
                to_vose_path = self.fileSystemService.join(vose_path, most_likely_genre, clean_name)

                if self.run_manifest and self.run_manifest.is_completed(folder):
                    counters["skip"] += 1
                    self.logger.info("Skipping '%s' (already completed in manifest)", folder)
                    self._log_stage_progress(
                        stage="RAW->TEMP",
                        current=index,
                        total=total_folders,
                        started_at=started_at,
                        current_name=clean_name,
                        counters=counters,
                    )
                    pbar.update(1)
                    continue

                try:
                    self._record_state(folder, "evaluating_destination")

                    if self._path_exists(to_vose_path):
                        counters["exists"] += 1
                        self.logger.info(
                            "[%d/%d] Exists in VOSE -> skip '%s'",
                            index,
                            total_folders,
                            clean_name,
                        )
                        status = (
                            "dry_run_skipped_existing_in_vose_precheck"
                            if self._is_dry_run()
                            else "skipped_existing_in_vose_precheck"
                        )
                        self._record_state(folder, status, {"destination": to_vose_path})
                    else:
                        self._record_state(folder, "moving_to_temp")
                        if self._is_dry_run():
                            counters["ok"] += 1
                            self.logger.info(
                                "[%d/%d] [DRY RUN] RAW -> TEMP | '%s' -> '%s'",
                                index,
                                total_folders,
                                from_path,
                                to_temp_path,
                            )
                            self._record_state(
                                folder,
                                "dry_run_would_move_to_temp",
                                {"temp_path": to_temp_path},
                            )
                        else:
                            self.fileSystemService.move(from_path, to_temp_path)
                            counters["ok"] += 1
                            self.logger.info(
                                "[%d/%d] RAW -> TEMP | '%s' -> '%s'",
                                index,
                                total_folders,
                                from_path,
                                to_temp_path,
                            )
                            self._record_state(
                                folder,
                                "moved_to_temp",
                                {"temp_path": to_temp_path},
                            )

                except Exception as exc:
                    counters["error"] += 1
                    self._record_state(folder, "conflict_or_error", {"error": str(exc)})
                    self.logger.exception("Failed processing '%s' in RAW->TEMP", folder)
                    raise

                self._log_stage_progress(
                    stage="RAW->TEMP",
                    current=index,
                    total=total_folders,
                    started_at=started_at,
                    current_name=clean_name,
                    counters=counters,
                )
                pbar.update(1)

        self.logger.info(
            "[RAW->TEMP][SUMMARY] total=%d ok=%d skip=%d exists=%d error=%d",
            total_folders,
            counters["ok"],
            counters["skip"],
            counters["exists"],
            counters["error"],
        )

    def renaming_in_temp(self) -> None:
        """
        Rename movie folders in TEMP to remove tags and resolve duplicates safely.
        """
        self._validate_services()

        if self._is_dry_run() and self._dry_run_temp_is_dirty:
            self.logger.warning(
                "Skipping renaming_in_temp() in DRY RUN because TEMP has stale content from previous runs."
            )
            return

        temp_path = self._get_temp_path(self.configService.getDirectorySource())
        self.fileSystemService.cd(temp_path)
        genres = sorted(self.fileSystemService.get_folders())

        self.logger.info("Renaming in TEMP across %d genres", len(genres))

        with tqdm(total=len(genres), desc="Renaming in TEMP", unit="genre") as pbar:
            for genre in genres:
                genre_path = self.fileSystemService.join(temp_path, genre)
                movies = sorted(self.fileSystemService.get_folders_at(genre_path))
                renamed_count = 0

                for movie in movies:
                    base_name = self.filterService.clean(movie)
                    old_path = self.fileSystemService.join(genre_path, movie)
                    new_name = base_name
                    new_path = self.fileSystemService.join(genre_path, new_name)

                    if old_path == new_path:
                        continue

                    counter = 1
                    while self._path_exists(new_path):
                        new_name = f"{base_name} ({counter})"
                        new_path = self.fileSystemService.join(genre_path, new_name)
                        counter += 1

                    try:
                        if not self._path_exists(old_path):
                            self.logger.warning("Skipping rename: source does not exist: %s", old_path)
                            continue

                        if self._is_dry_run():
                            self._record_state(
                                movie,
                                "dry_run_would_rename_in_temp",
                                {"from": old_path, "to": new_path},
                            )
                        else:
                            self.fileSystemService.rename(old_path, new_path)
                            renamed_count += 1
                            self._record_state(
                                movie,
                                "renamed_in_temp",
                                {"from": old_path, "to": new_path},
                            )
                    except Exception:
                        self.logger.exception("Failed renaming '%s' -> '%s'", movie, new_name)
                        raise

                self.logger.info("TEMP rename | genre=%s | movies=%d | renamed=%d", genre, len(movies), renamed_count)
                pbar.update(1)

    def moving_to_vose(self) -> None:
        """
        Merge TEMP into VOSE safely.

        Rules:
        - If destination movie folder does not exist, move the whole folder.
        - If destination movie folder exists:
            * copy only missing files
            * identical files are marked in source as AlreadyCopied_<name>
            * if real conflicts exist, skip that movie safely
        - Delete source folder only after verification succeeds.
        """
        self._validate_services()

        if self._is_dry_run() and self._dry_run_temp_is_dirty:
            self.logger.warning(
                "Skipping moving_to_vose() in DRY RUN because TEMP has stale content from previous runs."
            )
            return

        temp_path = self._get_temp_path(self.configService.getDirectorySource())
        vose_path = self.configService.getDirectoryTarget()

        self.fileSystemService.ensure_directory_exists(vose_path)
        genres = sorted(self.fileSystemService.get_folders_at(temp_path))

        total_movies = 0
        for genre in genres:
            genre_path = self.fileSystemService.join(temp_path, genre)
            total_movies += len(
                [movie for movie in self.fileSystemService.get_folders_at(genre_path) if not movie.startswith("@")]
            )

        counters = {"ok": 0, "skip": 0, "exists": 0, "conflict": 0, "error": 0}
        started_at = time.time()
        current_movie_idx = 0

        self.logger.info("TEMP->VOSE pending movies: %d", total_movies)

        with tqdm(total=total_movies, desc="TEMP -> VOSE", unit="movie") as pbar:
            for genre in genres:
                from_genre_path = self.fileSystemService.join(temp_path, genre)
                to_genre_path = self.fileSystemService.join(vose_path, genre)
                self.fileSystemService.ensure_directory_exists(to_genre_path)

                movies = sorted(
                    movie
                    for movie in self.fileSystemService.get_folders_at(from_genre_path)
                    if not movie.startswith("@")
                )

                for movie in movies:
                    current_movie_idx += 1
                    from_movie_path = self.fileSystemService.join(from_genre_path, movie)
                    to_movie_path = self.fileSystemService.join(to_genre_path, movie)

                    try:
                        result = self._move_or_merge_movie_folder(from_movie_path, to_movie_path)

                        if result == "skipped_existing_conflict":
                            counters["conflict"] += 1
                            self.logger.warning("Skipped conflicting existing movie: '%s'", movie)
                            self._record_state(
                                movie,
                                "skipped_existing_conflict",
                                {"destination": to_movie_path},
                            )

                        elif result == "dry_run_skipped_existing_conflict":
                            counters["conflict"] += 1
                            self.logger.warning(
                                "[DRY RUN] Existing conflicting movie would be skipped: '%s'",
                                movie,
                            )
                            self._record_state(
                                movie,
                                "dry_run_skipped_existing_conflict",
                                {"destination": to_movie_path},
                            )

                        elif result in ("dry_run_would_move", "dry_run_would_merge"):
                            counters["ok"] += 1
                            self._record_state(movie, result, {"destination": to_movie_path})

                        else:
                            counters["ok"] += 1
                            self.logger.info("VOSE transfer complete: '%s' [%s]", movie, result)
                            self._record_state(
                                movie,
                                "verified_and_source_deleted",
                                {"destination": to_movie_path},
                            )

                    except Exception as exc:
                        counters["error"] += 1
                        self._record_state(movie, "conflict_or_error", {"error": str(exc)})

                        if self._continue_on_error_enabled():
                            self.logger.exception("Error on '%s' (continuing)", movie)
                        else:
                            self.logger.exception("Stopping due to error on '%s'", movie)
                            raise

                    self._log_stage_progress(
                        stage="TEMP->VOSE",
                        current=current_movie_idx,
                        total=total_movies,
                        started_at=started_at,
                        current_name=movie,
                        counters=counters,
                    )
                    pbar.update(1)

        self.logger.info(
            "[TEMP->VOSE][SUMMARY] total=%d ok=%d conflict=%d error=%d",
            total_movies,
            counters["ok"],
            counters["conflict"],
            counters["error"],
        )

    def deleting_temp(self) -> None:
        """Delete TEMP after a successful run only if nothing pending remains."""
        self._validate_services()

        temp_path = self._get_temp_path(self.configService.getDirectorySource())
        if not self._path_exists(temp_path):
            self.logger.info("TEMP does not exist, nothing to delete: %s", temp_path)
            return

        if self._temp_has_pending_content(temp_path):
            self.logger.warning(
                "TEMP still contains pending/conflicting content. It will NOT be deleted: %s",
                temp_path,
            )
            return

        # Important on Windows:
        # move cwd OUTSIDE TEMP before trying to delete it
        safe_cwd = os.path.dirname(self.configService.getDirectorySource())
        if not safe_cwd:
            safe_cwd = os.getcwd()

        try:
            self.fileSystemService.cd(safe_cwd)
        except Exception:
            os.chdir(safe_cwd)

        try:
            if self._is_dry_run():
                self.logger.info("[DRY RUN] Would delete TEMP directory: %s", temp_path)
            else:
                self.fileSystemService.remove_directory(temp_path)
                self.logger.info("Deleted TEMP directory: %s", temp_path)
        except PermissionError:
            self.logger.warning(
                "TEMP could not be deleted because it is still in use. "
                "This is non-fatal; you can delete it manually later: %s",
                temp_path,
            )
        except Exception:
            self.logger.exception("Failed to delete TEMP directory '%s'", temp_path)
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _validate_services(self) -> None:
        missing = []
        if self.configService is None:
            missing.append("configService")
        if self.filterService is None:
            missing.append("filterService")
        if self.fileSystemService is None:
            missing.append("fileSystemService")
        if self.scrapperService is None:
            self.logger.warning(
                "scrapperService is not set; continuing because current workflow does not use it"
            )

        if missing:
            raise RuntimeError(f"MovieManager is missing required services: {', '.join(missing)}")

    def _record_state(self, movie_id: str, state: str, details: Dict | None = None) -> None:
        if self.run_manifest is None:
            return
        self.run_manifest.record_state(movie_id, state, details)

    def _is_dry_run(self) -> bool:
        return bool(self.configService and self.configService.is_dry_run())

    def _is_resume(self) -> bool:
        getter = getattr(self.configService, "is_resume", None)
        return bool(callable(getter) and getter())

    def _get_limit(self) -> int:
        getter = getattr(self.configService, "get_limit", None)
        if callable(getter):
            value = getter()
            return int(value) if value else 0
        return 0

    def _get_report_dir(self) -> str:
        getter = getattr(self.configService, "get_report_dir", None)
        if callable(getter):
            return getter()
        return "reports"

    def _continue_on_error_enabled(self) -> bool:
        getter = getattr(self.configService, "get_continue_on_error", None)
        return bool(callable(getter) and getter())

    def _get_temp_path(self, base_path: str) -> str:
        """
        Resolve TEMP path.

        Priority:
        1. config.directory_temp, if configured
        2. sibling directory next to RAW
        """
        configured_temp = ""
        if self.configService is not None:
            configured_temp = self.configService.getDirectoryTemp() or ""

        if configured_temp.strip():
            return os.path.abspath(configured_temp)

        raw_parent = os.path.dirname(os.path.abspath(base_path))
        temp_path = self.fileSystemService.join(raw_parent, self.TEMP_DIR_NAME)
        return os.path.abspath(temp_path)

    def _prepare_temp_directory(self, temp_path: str) -> None:
        self.logger.info("Preparing TEMP directory: %s", temp_path)
        self.fileSystemService.ensure_directory_exists(temp_path)
        self.fileSystemService.cd(temp_path)

    def _path_exists(self, path: str) -> bool:
        if hasattr(self.fileSystemService, "exists"):
            return bool(self.fileSystemService.exists(path))
        return os.path.exists(path)

    def _move_or_merge_movie_folder(self, from_movie_path: str, to_movie_path: str) -> str:
        """
        Return values:
        - moved_new
        - merged_and_deleted_source
        - skipped_existing_conflict
        - dry_run_would_move
        - dry_run_would_merge
        - dry_run_skipped_existing_conflict
        """
        if not self._path_exists(from_movie_path):
            raise FileNotFoundError(f"Source movie folder does not exist: {from_movie_path}")

        if not self._path_exists(to_movie_path):
            if self._is_dry_run():
                self.logger.info("[DRY RUN] Would move '%s' -> '%s'", from_movie_path, to_movie_path)
                return "dry_run_would_move"

            self.fileSystemService.move(from_movie_path, to_movie_path)
            if not self._path_exists(to_movie_path):
                raise RuntimeError(f"Move reported success but destination does not exist: {to_movie_path}")
            return "moved_new"

        missing, identical, conflicts = self._analyze_merge(from_movie_path, to_movie_path)

        if self._is_dry_run():
            if conflicts:
                return "dry_run_skipped_existing_conflict"
            return "dry_run_would_merge"

        # Safety-first rule:
        # If there are real conflicts, do NOT touch the source folder at all.
        if conflicts:
            self.logger.warning(
                "Existing destination has conflicts. Skipping source untouched: %s",
                from_movie_path,
            )
            self.logger.warning(self._format_conflicts(conflicts))
            return "skipped_existing_conflict"

        # Only after confirming there are NO conflicts do we mark identical files and copy missing ones.
        self._mark_identical_source_files(from_movie_path, identical)

        for rel_path in missing:
            src = self.fileSystemService.join(from_movie_path, rel_path)
            dst = self.fileSystemService.join(to_movie_path, rel_path)
            self.fileSystemService.copy_file(src, dst)

        self._verify_source_copied_to_destination(from_movie_path, to_movie_path)

        self.fileSystemService.remove_directory(from_movie_path)
        return "merged_and_deleted_source"

    def _analyze_merge(
        self,
        source_dir: str,
        destination_dir: str,
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Compare source vs destination by relative file path.

        Returns:
            missing_files: files absent in destination and must be copied.
            identical_files: files present in both places and judged equal.
            conflicts: files present in both places but different.
        """
        source_files = self._collect_relative_files(source_dir)
        destination_files = self._collect_relative_files(destination_dir)

        missing_files: List[str] = []
        identical_files: List[str] = []
        conflicts: List[str] = []

        for rel_path, source_size in source_files.items():
            if rel_path not in destination_files:
                missing_files.append(rel_path)
                continue

            destination_size = destination_files[rel_path]
            src_abs = self.fileSystemService.join(source_dir, rel_path)
            dst_abs = self.fileSystemService.join(destination_dir, rel_path)

            if source_size == destination_size and self._files_are_identical(src_abs, dst_abs):
                identical_files.append(rel_path)
            else:
                conflicts.append(
                    f"{rel_path} (source={source_size} bytes, destination={destination_size} bytes)"
                )

        return missing_files, identical_files, conflicts

    def _collect_relative_files(self, base_dir: str) -> Dict[str, int]:
        file_map: Dict[str, int] = {}

        def _recurse(current_dir: str, rel_base: str = "") -> None:
            for f in sorted(self.fileSystemService.get_files_at(current_dir)):
                if f.startswith(self.ALREADY_COPIED_PREFIX):
                    continue

                abs_f = self.fileSystemService.join(current_dir, f)
                rel_f = self.fileSystemService.join(rel_base, f) if rel_base else f
                file_map[rel_f] = self.fileSystemService.get_size(abs_f)

            for d in sorted(self.fileSystemService.get_folders_at(current_dir)):
                abs_d = self.fileSystemService.join(current_dir, d)
                rel_d = self.fileSystemService.join(rel_base, d) if rel_base else d
                _recurse(abs_d, rel_d)

        _recurse(base_dir)
        return file_map

    def _verify_source_copied_to_destination(self, source_dir: str, destination_dir: str) -> None:
        """
        Verify that every non-AlreadyCopied source file exists in destination with the same size.
        """
        source_files = self._collect_relative_files(source_dir)
        destination_files = self._collect_relative_files(destination_dir)

        missing_or_mismatched = []
        for rel_path, source_size in source_files.items():
            destination_size = destination_files.get(rel_path)
            if destination_size != source_size:
                missing_or_mismatched.append(
                    f"{rel_path} (source={source_size}, destination={destination_size})"
                )

        if missing_or_mismatched:
            raise RuntimeError(
                "Verification failed after merge. The following files are missing or mismatched in destination: "
                + "; ".join(missing_or_mismatched)
            )

    def _mark_identical_source_files(self, source_dir: str, identical_files: List[str]) -> None:
        """
        Rename identical source files to AlreadyCopied_<name> so retries can ignore them.
        """
        for rel_path in identical_files:
            src_abs = self.fileSystemService.join(source_dir, rel_path)
            if not self._path_exists(src_abs):
                continue

            parent_dir = os.path.dirname(src_abs)
            base_name = os.path.basename(src_abs)

            if base_name.startswith(self.ALREADY_COPIED_PREFIX):
                continue

            candidate_name = f"{self.ALREADY_COPIED_PREFIX}{base_name}"
            candidate_abs = self.fileSystemService.join(parent_dir, candidate_name)

            counter = 1
            while self._path_exists(candidate_abs):
                candidate_name = f"{self.ALREADY_COPIED_PREFIX}{counter}_{base_name}"
                candidate_abs = self.fileSystemService.join(parent_dir, candidate_name)
                counter += 1

            self.fileSystemService.rename(src_abs, candidate_abs)

    def _files_are_identical(self, source_path: str, destination_path: str) -> bool:
        """
        Safer SMB-friendly file equality check.

        Strategy:
        - size must match
        - files <= FULL_HASH_THRESHOLD: full SHA-256
        - larger files: compare SHA-256 of first and last SAMPLE_CHUNK_SIZE bytes
        """
        source_size = self.fileSystemService.get_size(source_path)
        destination_size = self.fileSystemService.get_size(destination_path)

        if source_size != destination_size:
            return False

        if source_size == 0:
            return True

        if source_size <= self.FULL_HASH_THRESHOLD:
            return self._sha256(source_path) == self._sha256(destination_path)

        return self._sample_signature(source_path, source_size) == self._sample_signature(
            destination_path,
            destination_size,
        )

    def _sha256(self, path: str) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(self.SAMPLE_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _sample_signature(self, path: str, size: int) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as f:
            head = f.read(self.SAMPLE_CHUNK_SIZE)
            digest.update(head)

            if size > self.SAMPLE_CHUNK_SIZE:
                seek_pos = max(0, size - self.SAMPLE_CHUNK_SIZE)
                f.seek(seek_pos)
                tail = f.read(self.SAMPLE_CHUNK_SIZE)
                digest.update(tail)

        digest.update(str(size).encode("utf-8"))
        return digest.hexdigest()

    def _format_conflicts(self, conflicts: Iterable[str]) -> str:
        conflicts_list = list(conflicts)
        preview = "; ".join(conflicts_list[:10])
        if len(conflicts_list) > 10:
            preview += f"; ... and {len(conflicts_list) - 10} more"
        return f"Merge conflict detected. Existing files differ from source: {preview}"

    def _temp_has_pending_content(self, temp_path: str) -> bool:
        """
        Return True if TEMP still contains files or movie folders that were not fully processed.
        Empty genre directories do not count as pending content.
        """
        if not self._path_exists(temp_path):
            return False

        genre_dirs = self.fileSystemService.get_folders_at(temp_path)
        for genre in genre_dirs:
            genre_path = self.fileSystemService.join(temp_path, genre)

            files_here = self.fileSystemService.get_files_at(genre_path)
            if files_here:
                return True

            movie_dirs = [
                d for d in self.fileSystemService.get_folders_at(genre_path)
                if not d.startswith("@")
            ]
            if movie_dirs:
                return True

        return False

    def _log_stage_progress(
        self,
        stage: str,
        current: int,
        total: int,
        started_at: float,
        current_name: str,
        counters: Dict[str, int],
        every: int = 25,
    ) -> None:
        """
        Compact progress line for long runs.
        Logs at:
        - first item
        - every N items
        - last item
        """
        if total <= 0:
            return

        if current != 1 and current != total and current % every != 0:
            return

        elapsed = max(0.001, time.time() - started_at)
        rate = current / elapsed
        remaining = total - current
        eta_seconds = int(remaining / rate) if rate > 0 else -1
        eta_str = "?:??" if eta_seconds < 0 else time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
        pct = (current / total) * 100

        self.logger.info(
            "[%s] %d/%d (%.1f%%) | ETA %s | ok=%d skip=%d exists=%d conflict=%d error=%d | %s",
            stage,
            current,
            total,
            pct,
            eta_str,
            counters.get("ok", 0),
            counters.get("skip", 0),
            counters.get("exists", 0),
            counters.get("conflict", 0),
            counters.get("error", 0),
            current_name,
        )