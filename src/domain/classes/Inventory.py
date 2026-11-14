"""Read-only inventory use case; reports one record per physical video path."""

import re
from dataclasses import dataclass
from pathlib import Path

from src.domain.classes.LibraryNames import (
    DIRECTOR_TAG,
    GENRE_TAG,
    VIDEO_SUFFIXES,
    clean_name,
    name_key,
    reserved,
    tag,
)
from src.domain.interfaces.LibraryFileSystem import LibraryReader

YEAR = re.compile(r"\(((?:18|19|20)\d{2})\)|\[((?:18|19|20)\d{2})\]")
LOOSE_YEAR = re.compile(r"(?<=[ ._-])((?:18|19|20)\d{2})(?=$|[ ._-])")
RELEASE = re.compile(
    r"\{edition-([^{}]+)\}|\b(director['’]?s[ ._-]+cut|extended[ ._-]+(?:cut|edition)"
    r"|theatrical[ ._-]+(?:cut|edition)|unrated|remastered|2160p|1080p|720p|4k"
    r"|blu[ ._-]?ray|web[ ._-]?(?:dl|rip)|x26[45]|hevc|hdr10?)\b",
    re.IGNORECASE,
)
EXTRA_DIRS = {
    "extra",
    "extras",
    "samples",
    "trailers",
    "featurettes",
    "shorts",
    "interviews",
    "deleted scenes",
    "behind the scenes",
    "behindthescenes",
    "scenes",
    "other",
}
EXTRA_FILE = re.compile(
    r"^(?:sample|trailer|featurette|teaser)(?:[ ._-]*\d+)?$"
    r"|(?:^|[ ._\-])(?:sample|trailer|featurette|teaser|deleted[ ._\-]*scene"
    r"|behind[ ._\-]*the[ ._\-]*scenes|interview)(?:[ ._\-]*\d+)?$"
    r"|[ ._]*-(?:scene|short|other)(?:[ ._\-]*\d+)?$",
    re.IGNORECASE,
)
GENERIC = re.compile(
    r"^(?:video|movie|feature|main|disc|part|cd)(?:[ ._-]*\d+)?$", re.I
)


@dataclass(frozen=True)
class Record:
    original_name: str
    original_folder: str
    title: str
    year: str
    genre: str
    director: str
    source_library: str
    path: str
    extension: str
    edition_release: str
    needs_review: bool


@dataclass(frozen=True)
class Parsed:
    title: str
    year: str
    releases: tuple[str, ...]
    uncertain: bool


def _parse(name: str) -> Parsed:
    clean = clean_name(name)
    releases = tuple(
        " ".join(re.split(r"[ ._]+", (m[1] or m[2]).strip()))
        for m in RELEASE.finditer(clean)
    )
    # Ignore a year embedded in a title with no context (e.g. "Blade Runner 2049").
    explicit = [m for m in YEAR.finditer(clean) if clean[: m.start()].strip()]
    hint = RELEASE.search(clean)
    loose = [
        m
        for m in LOOSE_YEAR.finditer(clean)
        if clean[: m.start()].strip()
        and ("." in clean[: m.start()] or (hint and hint.start() > m.end()))
    ]
    candidates = explicit or loose
    if candidates:
        match = candidates[-1]
        title = clean[: match.start()].rstrip(" ._-")
        year = next(group for group in match.groups() if group)
    else:
        title = clean
        year = ""
        if hint and clean[: hint.start()].strip(" ._-[({"):
            title = clean[: hint.start()].rstrip(" ._-[({")
    if "." in title and " " not in title:
        title = title.replace(".", " ")
    return Parsed(title or name, year, releases, not explicit or len(candidates) > 1)


class Inventory:
    def __init__(self, reader: LibraryReader, genres: dict[str, str]) -> None:
        self.reader = reader
        self.genres = genres

    def scan(self, roots: dict[str, Path]) -> list[Record]:
        return [
            record
            for label, root in roots.items()
            for record in self._scan_root(label, root)
        ]

    def _scan_root(self, label: str, root: Path):
        pending = [root]
        while pending:
            directory = pending.pop()
            children = self.reader.entries(directory)
            pending.extend(
                entry.path
                for entry in reversed(children)
                if entry.kind == "directory"
                and not reserved(entry.path.name)
                and name_key(re.sub(r"[_.-]+", " ", entry.path.name)) not in EXTRA_DIRS
            )
            for entry in children:
                path = entry.path
                if (
                    entry.kind == "file"
                    and not reserved(path.name)
                    and path.suffix.lower() in VIDEO_SUFFIXES
                    and not EXTRA_FILE.search(path.stem)
                ):
                    yield self._record(label, root, path)

    def _record(self, label: str, root: Path, path: Path) -> Record:
        file = _parse(path.stem)
        folders = path.relative_to(root).parts[:-1]
        genre = tag(GENRE_TAG, path.stem)
        director = tag(DIRECTOR_TAG, path.stem)
        for folder in reversed(folders):
            genre = genre or tag(GENRE_TAG, folder)
            director = director or tag(DIRECTOR_TAG, folder)
        if folders:
            genre = genre or self.genres.get(name_key(folders[0]), "")
        parent = _parse(folders[-1]) if folders else None
        title, year = file.title, file.year
        uncertain = file.uncertain
        if parent:
            same_title = name_key(parent.title) == name_key(file.title)
            if GENERIC.fullmatch(file.title) and parent.year:
                title, year = parent.title, parent.year
                uncertain = True
            elif same_title and not year:
                year = parent.year
                uncertain = parent.uncertain
            elif same_title and year and parent.year and year != parent.year:
                uncertain = True
        editions = dict.fromkeys((*file.releases, *(parent.releases if parent else ())))
        return Record(
            path.name,
            folders[-1] if folders else "",
            title,
            year,
            genre,
            director,
            label,
            str(path),
            path.suffix.lower(),
            "; ".join(editions),
            uncertain,
        )
