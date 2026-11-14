"""Validation shared by the filesystem and the CLI's output adapter."""

import os
import stat
from pathlib import Path
from typing import Iterable


def inspect(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def no_links(path: Path) -> None:
    for part in (*reversed(path.parents), path):
        info = inspect(part)
        if info is not None and is_link(info):
            raise ValueError(f"Symlink or reparse point is not allowed: {part}")


def contains(root: Path, path: Path) -> bool:
    return path == root or root in path.parents


def aliases(root: Path, path: Path) -> bool:
    """Also catch existing aliases (e.g. a Windows drive and a UNC path)."""
    if contains(root, path):
        return True
    root_info = inspect(root)
    if root_info is None or not root_info.st_ino:
        # Compare the first existing ancestor if the configured root is absent.
        if (
            root_info is None
            and root.parent != root
            and inspect(root.parent) is not None
        ):
            parent_info = root.parent.stat()
            return bool(parent_info.st_ino) and any(
                part.name.casefold() == root.name.casefold()
                and (info := inspect(part.parent)) is not None
                and os.path.samestat(parent_info, info)
                for part in (path, *path.parents)
            )
        return False
    return any(
        (info := inspect(part)) is not None and os.path.samestat(root_info, info)
        for part in (path, *path.parents)
    )


def reject_windows_streams(path: Path) -> None:
    if os.name == "nt" and any(":" in part for part in path.parts[1:]):
        raise ValueError(f"Windows alternate streams are not supported: {path}")


def library_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts or path == Path(path.anchor):
        raise ValueError(
            f"Expected an absolute library directory below the filesystem root: {value!r}"
        )
    reject_windows_streams(path)
    no_links(path)
    return path


def validate_roots(roots: dict[str, Path], optional: Iterable[str] = ()) -> None:
    optional = set(optional)
    for label, path in roots.items():
        no_links(path)
        info = inspect(path)
        if info is None:
            if label not in optional:
                raise FileNotFoundError(f"{label} directory does not exist: {path}")
            if not path.parent.is_dir():
                raise FileNotFoundError(
                    f"Parent of {label} does not exist: {path.parent}"
                )
        elif not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError(f"{label} is not a directory: {path}")
    items = list(roots.items())
    for index, (label, path) in enumerate(items):
        for other_label, other_path in items[:index]:
            if aliases(path, other_path) or aliases(other_path, path):
                raise ValueError(
                    f"Library roots must not overlap: {label}={path}, {other_label}={other_path}"
                )


def output_path(value: str | Path, protected: Iterable[Path]) -> Path:
    path = Path(os.path.abspath(Path(value).expanduser()))
    reject_windows_streams(path)
    no_links(path)
    for root in protected:
        if aliases(root, path):
            raise ValueError(f"Output must be outside all library roots: {path}")
    return path
