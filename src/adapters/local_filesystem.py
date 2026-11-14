"""Local library adapter shared by the Synology, macOS, and Windows entry points."""

import errno
import hashlib
import logging
import os
import shutil
import stat
from contextlib import contextmanager
from pathlib import Path

from src.adapters.native_rename import rename_noreplace
from src.adapters.paths import (
    contains,
    inspect,
    is_link,
    no_links,
    reject_windows_streams,
)
from src.domain.classes.LibraryNames import LOCK_NAME, staging_name
from src.domain.interfaces.IFileSystemInterface import IFileSystem
from src.domain.interfaces.LibraryFileSystem import Entry


logger = logging.getLogger(__name__)


def _entry(path: Path, info: os.stat_result) -> Entry:
    if is_link(info):
        kind = "link"
    elif stat.S_ISDIR(info.st_mode):
        kind = "directory"
    elif stat.S_ISREG(info.st_mode):
        kind = "file"
    else:
        kind = "special"
    return Entry(path, kind, info.st_size, info.st_mtime_ns)


def _signature(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _sha256(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.digest()


def _sync_directory(path: Path) -> None:
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


class LocalFileSystem(IFileSystem):
    """Mutations require explicit authorization and validated library boundaries."""

    def __init__(self, *, apply: bool = False, roots: tuple[Path, ...] = ()) -> None:
        self._cwd = Path.cwd()
        self._apply = apply
        self._roots = roots
        self._filter_service = None
        self._config_service = None

    @property
    def writable(self) -> bool:
        return self._apply and (
            self._config_service is None or not self._config_service.is_dry_run()
        )

    def _guard(self, path: Path, *, allow_root: bool = False) -> None:
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not any(
                contains(root, path) and (allow_root or path != root)
                for root in self._roots
            )
        ):
            raise ValueError(f"Write outside an authorized library path: {path}")
        reject_windows_streams(path)
        no_links(path)

    def entry(self, path: Path) -> Entry | None:
        no_links(path.parent)
        info = inspect(path)
        return _entry(path, info) if info is not None else None

    def entries(self, path: Path) -> list[Entry]:
        no_links(path)
        with os.scandir(path) as children:
            return sorted(
                (
                    _entry(path / child.name, child.stat(follow_symlinks=False))
                    for child in children
                ),
                key=lambda entry: (entry.path.name.casefold(), entry.path.name),
            )

    def _snapshot(self, path: Path) -> dict[Path, os.stat_result]:
        no_links(path)
        root = path.lstat()
        result = {}
        pending = [path]
        while pending:
            current = pending.pop()
            info = current.lstat()
            kind = _entry(current, info).kind
            if (
                kind not in {"directory", "file"}
                or info.st_dev != root.st_dev
                or (current != path and kind == "directory" and current.is_mount())
            ):
                raise ValueError(
                    f"Cannot transfer a link, special file or nested mount: {current}"
                )
            result[current.relative_to(path)] = info
            if kind == "directory":
                pending.extend(child.path for child in reversed(self.entries(current)))
        return result

    def tree(self, path: Path) -> dict[Path, Entry]:
        return {
            relative: _entry(path / relative, info)
            for relative, info in self._snapshot(path).items()
        }

    def same_content(self, first: Entry, second: Entry) -> bool:
        no_links(first.path)
        no_links(second.path)
        return first.size == second.size and _sha256(first.path) == _sha256(second.path)

    def make_directory(self, path: Path) -> None:
        if self.writable:
            self._guard(path, allow_root=True)
            path.mkdir(exist_ok=True)
            _sync_directory(path.parent)

    @contextmanager
    def lock(self, raw: Path):
        """Serialize runs sharing RAW. A hard interruption leaves a visible lock."""
        path = raw / LOCK_NAME
        if not self.writable:
            yield
            return
        self._guard(path)
        with path.open("x", encoding="utf-8") as stream:
            try:
                stream.write(f"pid={os.getpid()}\n")
                stream.flush()
                yield
            finally:
                # Windows cannot unlink the file while our handle is open.
                stream.close()
                path.unlink()

    def transfer(self, source: Path, destination: Path) -> None:
        if not self.writable:
            return
        self._check_transfer(source, destination)
        self._check_staging(destination)
        snapshot = self._snapshot(source)
        try:
            rename_noreplace(source, destination)
        except OSError as exc:
            if exc.errno != errno.EXDEV and getattr(exc, "winerror", None) != 17:
                raise
            self._verified_copy(source, destination, snapshot, remove_source=True)
        else:
            _sync_directory(destination.parent)
            if source.parent != destination.parent:
                _sync_directory(source.parent)

    def _check_transfer(self, source: Path, destination: Path) -> None:
        self._guard(source)
        self._guard(destination)
        if contains(source, destination) or contains(destination, source):
            raise ValueError(f"Transfer paths overlap: {source} -> {destination}")
        if inspect(destination) is not None:
            raise FileExistsError(
                errno.EEXIST, "Destination already exists", str(destination)
            )
        if not destination.parent.is_dir():
            raise NotADirectoryError(
                f"Destination parent is not a directory: {destination.parent}"
            )

    def _check_staging(self, destination: Path) -> Path:
        staging = destination.with_name(staging_name(destination.name))
        if inspect(staging) is not None:
            raise FileExistsError(
                f"Interrupted transfer staging needs review: {staging}"
            )
        return staging

    def _verified_copy(
        self,
        source: Path,
        destination: Path,
        snapshot: dict[Path, os.stat_result],
        *,
        remove_source: bool,
    ) -> None:
        """Publish a complete tree before unlinking any source file."""
        staging = self._check_staging(destination)
        staging.mkdir(mode=0o700)
        payload = staging / "payload"
        hashes = {}
        logger.info("Staging cross-filesystem copy at %s", staging)
        try:
            for relative, info in snapshot.items():
                src, dst = source / relative, payload / relative
                no_links(src)
                if stat.S_ISDIR(info.st_mode):
                    dst.mkdir()
                else:
                    shutil.copyfile(src, dst, follow_symlinks=False)
                    no_links(dst)
                    with dst.open("rb+") as stream:
                        shutil.copystat(src, dst, follow_symlinks=False)
                        os.fsync(stream.fileno())
                    hashes[relative] = _sha256(src)
            copied = self._snapshot(payload)
            if copied.keys() != snapshot.keys() or any(
                not stat.S_ISREG(copied[relative].st_mode)
                or copied[relative].st_size != snapshot[relative].st_size
                or _sha256(payload / relative) != expected
                for relative, expected in hashes.items()
            ):
                raise OSError("Copy verification failed")
            current = self._snapshot(source)
            if current.keys() != snapshot.keys() or any(
                _signature(current[relative]) != _signature(info)
                for relative, info in snapshot.items()
            ):
                raise OSError("Source changed during copy")
            for relative, info in reversed(list(snapshot.items())):
                if stat.S_ISDIR(info.st_mode):
                    shutil.copystat(
                        source / relative, payload / relative, follow_symlinks=False
                    )
                    _sync_directory(payload / relative)
            _sync_directory(staging)
            self._check_transfer(source, destination)
            rename_noreplace(payload, destination)
            _sync_directory(destination.parent)
            if remove_source:
                self._remove_verified_source(source, destination, snapshot, copied)
                _sync_directory(source.parent)
            staging.rmdir()
        except (OSError, ValueError) as exc:
            message = (
                f"{source} -> {destination}: {exc}; inspect staging at {staging}. "
                "Source cleanup is only attempted after verified publication."
            )
            if isinstance(exc, FileExistsError):
                raise FileExistsError(message) from exc
            raise OSError(message) from exc

    def _remove_verified_source(self, source, destination, snapshot, copied) -> None:
        # On an interrupted cleanup the remaining source is visible; the final copy is complete.
        for relative, info in reversed(list(snapshot.items())):
            src = source / relative
            self._guard(src)
            if stat.S_ISDIR(info.st_mode):
                src.rmdir()  # Never remove an unexpected file.
            else:
                dst = destination / relative
                self._guard(dst)
                dst_info = dst.lstat()
                expected = copied[relative]
                if (
                    _signature(src.lstat()) != _signature(info)
                    or _signature(dst_info)[:-1] != _signature(expected)[:-1]
                ):
                    raise OSError(
                        f"Source or published file changed before cleanup: {src}"
                    )
                src.unlink()

    # Compatibility with the existing generic filesystem port. The workflow uses
    # absolute paths through LibraryFileSystem and never changes the process cwd.
    def _absolute(self, path: str) -> Path:
        return Path(os.path.abspath(self._cwd / path))

    def exists(self, path: str) -> bool:
        return self.entry(self._absolute(path)) is not None

    def is_file(self, path: str) -> bool:
        entry = self.entry(self._absolute(path))
        return entry is not None and entry.kind == "file"

    def is_dir(self, path: str) -> bool:
        entry = self.entry(self._absolute(path))
        return entry is not None and entry.kind == "directory"

    def get_size(self, path: str) -> int:
        entry = self.entry(self._absolute(path))
        if entry is None or entry.kind != "file":
            raise FileNotFoundError(path)
        return entry.size

    def cd(self, path: str) -> None:
        if not self.is_dir(path):
            raise NotADirectoryError(path)
        self._cwd = self._absolute(path)

    def back(self) -> str:
        self.cd(str(self._cwd.parent))
        return self.pwd()

    def pwd(self) -> str:
        return str(self._cwd)

    def get_folders_at(self, path: str) -> list[str]:
        return [
            entry.path.name
            for entry in self.entries(self._absolute(path))
            if entry.kind == "directory"
        ]

    def get_files_at(self, path: str) -> list[str]:
        return [
            entry.path.name
            for entry in self.entries(self._absolute(path))
            if entry.kind == "file"
        ]

    def get_folders(self) -> list[str]:
        return self.get_folders_at(self.pwd())

    list_directories = get_folders

    def get_folder(self, folder_name: str) -> str:
        return str(self._absolute(folder_name))

    def ensure_directory_exists(self, path: str) -> None:
        self.make_directory(self._absolute(path))

    mkdir = create_folder = ensure_directory_exists

    def create_folders(self, folders: list[str]) -> None:
        for folder in folders:
            self.create_folder(folder)

    def remove_file(self, path: str) -> None:
        if self.writable:
            target = self._absolute(path)
            self._guard(target)
            target.unlink()

    def remove_directory(self, path: str) -> None:
        if self.writable:
            target = self._absolute(path)
            self._guard(target)
            target.rmdir()

    rmdir = delete_folder = remove_directory

    def delete_folders(self, folders: list[str]) -> None:
        for folder in folders:
            self.delete_folder(folder)

    def move(self, from_path: str, to_path: str) -> None:
        self.transfer(self._absolute(from_path), self._absolute(to_path))

    rename = deep_tree_move = move_folder = move

    def move_folders(self, folders: list[str], destination_path: str) -> None:
        for folder in folders:
            self.move(folder, self.join(destination_path, self._absolute(folder).name))

    def copy_file(self, src: str, dst: str) -> None:
        if self.writable:
            source, destination = self._absolute(src), self._absolute(dst)
            self._check_transfer(source, destination)
            snapshot = self._snapshot(source)
            if not stat.S_ISREG(snapshot[Path(".")].st_mode):
                raise ValueError(f"Not a regular file: {source}")
            self._verified_copy(source, destination, snapshot, remove_source=False)

    def join(self, *paths: str) -> str:
        return os.path.join(*paths)

    def setConfig(self, config) -> None:
        self._config_service = config

    def getConfig(self):
        return self._config_service

    def setFilter(self, service) -> None:
        self._filter_service = service

    def getFilter(self):
        return self._filter_service

    def hasFilter(self) -> bool:
        return self._filter_service is not None
