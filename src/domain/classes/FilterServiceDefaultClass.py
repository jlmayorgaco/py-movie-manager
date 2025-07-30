import re
import logging
from Levenshtein import distance
from typing import List

from src.domain.interfaces.IFilterServiceInterface import IFilterService


class FilterServiceDefault(IFilterService):
    """
    FilterServiceDefault: A service to handle filtering operations for genres and directors,
    including cleaning folder names and finding the most similar genres.
    """

    def __init__(self):
        """
        Initialize the FilterServiceDefault with default values.
        """
        self.search_genre_tag = ''
        self.search_director_tag = ''
        self.genres: List[str] = []
        self.logger = logging.getLogger(__name__)  # ✅ Logger added

    def __str__(self) -> str:
        """
        String representation of the filter service, showing current tags.
        """
        return (
            f"FilterServiceDefault::search_genre_tag <{self.search_genre_tag}>\n"
            f"FilterServiceDefault::search_director_tag <{self.search_director_tag}>"
        )

    # Setter Methods
    def setGenres(self, genres: List[str]) -> None:
        """
        Set the list of genres.

        Args:
            genres (List[str]): List of genres to set.
        """
        self.genres = genres

    def setGenreSearchTag(self, tag: str) -> None:
        """
        Set the genre search tag.

        Args:
            tag (str): Genre search tag to set.
        """
        self.search_genre_tag = tag

    def setDirectorSearchTag(self, tag: str) -> None:
        """
        Set the director search tag.

        Args:
            tag (str): Director search tag to set.
        """
        self.search_director_tag = tag

    # Core Functionality
    def getGenreByMostLikehood(self, genre: str) -> str:  # ✅ Fixed method name
        """
        Find the most similar genre to the provided one based on Levenshtein distance.

        Args:
            genre (str): Genre string to compare.

        Returns:
            str: The most similar genre.
        """
        if not self.genres:
            raise ValueError("Genres list is empty. Ensure genres are set before calling this method.")

        if genre == "Unknown":
            self.logger.info("Skipping genre matching because genre is 'Unknown'.")
            return "Unknown"

        most_similar = min(self.genres, key=lambda x: distance(x.upper(), genre.upper()))
        self.logger.info(f"Matching genre '{genre}' -> Most likely: '{most_similar}'")
        return most_similar

    def clean(self, folder_string: str) -> str:
        """
        Clean a folder string by removing tags and trimming whitespace.

        Args:
            folder_string (str): The folder string to clean.

        Returns:
            str: The cleaned folder string.
        """
        pattern = re.compile(r'^\[g-(.*?)\]\[d-(.*?)\]')
        cleaned_folder = re.sub(pattern, '', folder_string).strip()
        return cleaned_folder

    def getGenreByFolderName(self, folder_name: str) -> str:
        """
        Extract the genre from a folder name based on the genre tag.

        Args:
            folder_name (str): Folder name to parse.

        Returns:
            str: Extracted genre or 'Unknown' if not found.
        """
        match = re.search(r'\[g-(.*?)\]', folder_name)
        genre = match.group(1) if match else "Unknown"
        self.logger.info(f"Extracted genre '{genre}' from folder '{folder_name}'")
        return genre

    def extractTags(self, folder_name: str) -> dict:
        """
        Extract genre and director tags from a folder name.

        Args:
            folder_name (str): Folder name to parse.

        Returns:
            dict: Dictionary with extracted tags {'genre': ..., 'director': ...}.
        """
        pattern = re.compile(r'\[g-(.*?)\]\[d-(.*?)\]')
        match = re.search(pattern, folder_name)
        if match:
            return {'genre': match.group(1), 'director': match.group(2)}
        return {'genre': "Unknown", 'director': "Unknown"}

    def filter_folders(self, folders: List[str]) -> List[str]:
        """
        Filters folders to include only those that contain a valid genre tag.

        Args:
            folders (List[str]): List of folder names to filter.

        Returns:
            List[str]: A filtered list containing only folders with valid genre tags.
        """
        filtered_folders = []
        for folder in folders:
            genre = self.getGenreByFolderName(folder)
            if genre != "Unknown":
                filtered_folders.append(folder)
            else:
                self.logger.info(f"Skipping folder '{folder}': No valid genre tag found.")

        self.logger.info(f"Filtered {len(filtered_folders)}/{len(folders)} folders with valid genre tags.")
        return filtered_folders
    
    def clean_folder_name(self, name: str) -> str:
        """
        Remove [g-*], [d-*], and similar tags from the folder name.
        """
        # Remove tags like [g-Animation] or [d-John Smith]
        cleaned = re.sub(r"\[.*?\]", "", name)
        # Remove extra spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned