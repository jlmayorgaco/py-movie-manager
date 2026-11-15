"""Parse movie folder tags and resolve genres using explicit names and aliases."""

from __future__ import annotations

import re
import unicodedata

from config.GenresConfig import GENRE_ALIASES, GenresEnum
from src.domain.classes.LibraryNames import DIRECTOR_TAG, GENRE_TAG, clean_name
from src.domain.interfaces.IFilterServiceInterface import IFilterService


def _genre_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    plain = "".join(
        " " if char in "._" or unicodedata.category(char) == "Pd" else char
        for char in decomposed
        if not unicodedata.combining(char)
    )
    return " ".join(plain.split())


def _edit_distance(left: str, right: str) -> int:
    """Levenshtein distance for review suggestions only."""
    row = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        previous, row[0] = row[0], i
        for j, b in enumerate(right, 1):
            current = row[j]
            row[j] = min(current + 1, row[j - 1] + 1, previous + (a != b))
            previous = current
    return row[-1]


def _build_genre_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    for genre in GenresEnum:
        canonical = _genre_key(genre.name)
        for label in (genre.name, genre.value, *GENRE_ALIASES.get(genre, ())):
            key = _genre_key(label)
            existing = keys.setdefault(key, canonical)
            if existing != canonical:
                raise ValueError(
                    f"Genre label {label!r} maps to {existing!r} and {canonical!r}"
                )
    return keys


_GENRE_KEYS = _build_genre_keys()


class FilterServiceDefault(IFilterService):
    TAG_PAIR_PREFIX_PATTERN = re.compile(r"^\[g-(.*?)\]\[d-(.*?)\]", re.IGNORECASE)
    MULTISPACE_PATTERN = re.compile(r"\s{2,}")

    def __init__(self) -> None:
        self.search_genre_tag = ""
        self.search_director_tag = ""
        self.genres: list[str] = []
        self._configured_genres: dict[str, str] = {}

    def __str__(self) -> str:
        return (
            f"FilterServiceDefault::search_genre_tag <{self.search_genre_tag}>\n"
            f"FilterServiceDefault::search_director_tag <{self.search_director_tag}>"
        )

    def setGenres(self, genres: list[str]) -> None:
        self.genres = genres or []
        self._configured_genres = {_genre_key(genre): genre for genre in self.genres}

    def setGenreSearchTag(self, tag: str) -> None:
        self.search_genre_tag = tag or ""

    def setDirectorSearchTag(self, tag: str) -> None:
        self.search_director_tag = tag or ""

    def resolve_genre(self, genre: str) -> str | None:
        """Resolve an exact normalized label or alias to a configured genre."""
        key = _genre_key(genre)
        return self._configured_genres.get(_GENRE_KEYS.get(key, key))

    def suggest_genres(self, genre: str) -> tuple[str, ...]:
        """Suggest configured genres within one edit of an explicit label."""
        key = _genre_key(genre)
        if len(key) < 3 or self.resolve_genre(genre) is not None:
            return ()
        labels = {**{label: label for label in self._configured_genres}, **_GENRE_KEYS}
        return tuple(
            sorted(
                {
                    self._configured_genres[canonical]
                    for label, canonical in labels.items()
                    if canonical in self._configured_genres
                    and abs(len(key) - len(label)) <= 1
                    and _edit_distance(key, label) == 1
                }
            )
        )

    def getGenreByMostLikehood(self, genre: str | None) -> str:
        """Legacy name retained for callers; unknown genres are not guessed."""
        return self.resolve_genre(genre or "") or "Unknown"

    getGenreByMostLikelihood = getGenreByMostLikehood

    def genre_tag(self, folder_name: str) -> str | None:
        """Return the tag text, or None if the folder has no genre tag."""
        match = GENRE_TAG.search(folder_name or "")
        return match.group(1) if match else None

    def getGenreByFolderName(self, folder_name: str) -> str:
        return (self.genre_tag(folder_name) or "").strip() or "Unknown"

    def clean(self, folder_string: str) -> str:
        """Remove the leading [g-*][d-*] tag pair and normalize whitespace."""
        text = (folder_string or "").strip()
        cleaned = self.TAG_PAIR_PREFIX_PATTERN.sub("", text).strip()
        return self.MULTISPACE_PATTERN.sub(" ", cleaned).strip()

    def extractTags(self, folder_name: str) -> dict:
        """Extract both genre and director tags from a folder name."""
        director = DIRECTOR_TAG.search(folder_name or "")
        return {
            "genre": self.getGenreByFolderName(folder_name),
            "director": director.group(1).strip() if director else "Unknown",
        }

    def filter_folders(self, folders: list[str]) -> list[str]:
        """Keep only folders whose genre tags resolve to a configured genre."""
        return [
            folder
            for folder in folders
            if self.resolve_genre(self.getGenreByFolderName(folder)) is not None
        ]

    def clean_folder_name(self, name: str) -> str:
        """Remove genre and director metadata while preserving edition tags."""
        return clean_name(name or "")
