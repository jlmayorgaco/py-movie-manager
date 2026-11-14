"""Ports for the organization and inventory use cases."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Entry:
    path: Path
    kind: str  # directory, file, link, or special
    size: int
    modified_ns: int


class LibraryReader(Protocol):
    def entry(self, path: Path) -> Entry | None: ...
    def entries(self, path: Path) -> list[Entry]: ...


class LibraryFileSystem(LibraryReader, Protocol):
    def tree(self, path: Path) -> dict[Path, Entry]: ...
    def same_content(self, first: Entry, second: Entry) -> bool: ...
    def make_directory(self, path: Path) -> None: ...
    def transfer(self, source: Path, destination: Path) -> None: ...
