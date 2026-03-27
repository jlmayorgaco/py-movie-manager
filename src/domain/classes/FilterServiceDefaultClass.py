import logging
import re
from typing import List

from Levenshtein import distance

from src.domain.interfaces.IFilterServiceInterface import IFilterService


class FilterServiceDefault(IFilterService):
    """
    FilterServiceDefault: handles folder-name parsing, genre extraction,
    tag extraction, folder filtering, and cleaning of movie folder names.
    """

    # Precompiled regex patterns for performance and clarity
    GENRE_TAG_PATTERN = re.compile(r"\[g-(.*?)\]", re.IGNORECASE)
    DIRECTOR_TAG_PATTERN = re.compile(r"\[d-(.*?)\]", re.IGNORECASE)
    TAG_PAIR_PREFIX_PATTERN = re.compile(r"^\[g-(.*?)\]\[d-(.*?)\]", re.IGNORECASE)
    ANY_TAG_PATTERN = re.compile(r"\[.*?\]")
    MULTISPACE_PATTERN = re.compile(r"\s{2,}")

    def __init__(self) -> None:
        self.search_genre_tag = ""
        self.search_director_tag = ""
        self.genres: List[str] = []
        self.logger = logging.getLogger(__name__)

    def __str__(self) -> str:
        return (
            f"FilterServiceDefault::search_genre_tag <{self.search_genre_tag}>\n"
            f"FilterServiceDefault::search_director_tag <{self.search_director_tag}>"
        )

    # ------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------
    def setGenres(self, genres: List[str]) -> None:
        self.genres = genres or []
        self.logger.debug("Configured %d genres.", len(self.genres))

    def setGenreSearchTag(self, tag: str) -> None:
        self.search_genre_tag = tag or ""
        self.logger.debug("Configured genre search tag: %s", self.search_genre_tag)

    def setDirectorSearchTag(self, tag: str) -> None:
        self.search_director_tag = tag or ""
        self.logger.debug("Configured director search tag: %s", self.search_director_tag)

    # ------------------------------------------------------------------
    # Core functionality
    # ------------------------------------------------------------------
    def getGenreByMostLikehood(self, genre: str) -> str:
        """
        Return the closest configured genre using Levenshtein distance.

        Keeps legacy method name for compatibility with the rest of the project.
        """
        if not self.genres:
            raise ValueError(
                "Genres list is empty. Ensure genres are set before calling this method."
            )

        normalized_genre = (genre or "").strip()
        if not normalized_genre or normalized_genre == "Unknown":
            self.logger.debug("Skipping genre similarity match because genre is unknown/empty.")
            return "Unknown"

        most_similar = min(
            self.genres,
            key=lambda x: distance(str(x).upper(), normalized_genre.upper()),
        )
        self.logger.debug(
            "Genre similarity match: input='%s' -> selected='%s'",
            normalized_genre,
            most_similar,
        )
        return most_similar

    def clean(self, folder_string: str) -> str:
        """
        Remove the leading [g-*][d-*] tag pair and normalize whitespace.
        """
        text = (folder_string or "").strip()
        cleaned = self.TAG_PAIR_PREFIX_PATTERN.sub("", text).strip()
        cleaned = self.MULTISPACE_PATTERN.sub(" ", cleaned)
        return cleaned.strip()

    def getGenreByFolderName(self, folder_name: str) -> str:
        """
        Extract the genre tag from a folder name.
        Returns 'Unknown' if no [g-*] tag is found.
        """
        text = folder_name or ""
        match = self.GENRE_TAG_PATTERN.search(text)
        genre = match.group(1).strip() if match else "Unknown"
        self.logger.debug("Extracted genre '%s' from folder '%s'", genre, folder_name)
        return genre

    def extractTags(self, folder_name: str) -> dict:
        """
        Extract both genre and director tags from a folder name.
        """
        text = folder_name or ""

        genre_match = self.GENRE_TAG_PATTERN.search(text)
        director_match = self.DIRECTOR_TAG_PATTERN.search(text)

        genre = genre_match.group(1).strip() if genre_match else "Unknown"
        director = director_match.group(1).strip() if director_match else "Unknown"

        self.logger.debug(
            "Extracted tags from '%s' -> genre='%s', director='%s'",
            folder_name,
            genre,
            director,
        )

        return {
            "genre": genre,
            "director": director,
        }

    def filter_folders(self, folders: List[str]) -> List[str]:
        """
        Keep only folders that contain a valid [g-*] tag.
        """
        filtered_folders: List[str] = []
        skipped_count = 0

        for folder in folders:
            genre = self.getGenreByFolderName(folder)
            if genre != "Unknown":
                filtered_folders.append(folder)
            else:
                skipped_count += 1
                self.logger.debug(
                    "Skipping folder '%s': no valid genre tag found.",
                    folder,
                )

        self.logger.info(
            "Folder filter summary: valid=%d skipped=%d total=%d",
            len(filtered_folders),
            skipped_count,
            len(folders),
        )
        return filtered_folders

    def clean_folder_name(self, name: str) -> str:
        """
        Remove [g-*], [d-*], and any other bracket tags from folder names,
        then normalize whitespace.
        """
        text = (name or "").strip()
        cleaned = self.ANY_TAG_PATTERN.sub("", text)
        cleaned = self.MULTISPACE_PATTERN.sub(" ", cleaned)
        return cleaned.strip()