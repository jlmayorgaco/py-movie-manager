from typing import List
import json
import os
from src.domain.interfaces.IConfigInterface import IConfig
from config.GenresConfig import GenresEnum


class Config(IConfig):
    """
    Config: A class to manage configuration for directory paths and genres.

    This class encapsulates configuration settings such as the source and target 
    directories for movie organization, as well as the genres to be used for classification.
    """

    def __init__(self, config_file: str = "config/config.json"):
        """
        Initialize the Config class with default values or from JSON config file.
        """
        self._directory_raw: str = ""
        self._directory_temp: str = ""
        self._directory_vose: str = ""
        self._genres: List[GenresEnum] = []
        self._dry_run: bool = False
        self._config_file = config_file

        self._load_from_json()

    def _load_from_json(self) -> None:
        """
        Load configuration values from a JSON file.
        """
        if not os.path.exists(self._config_file):
            raise FileNotFoundError(f"Config file not found: {self._config_file}")

        with open(self._config_file, "r") as f:
            data = json.load(f)

        self._directory_raw = data.get("directory_raw", "")
        self._directory_temp = data.get("directory_temp", "")
        self._directory_vose = data.get("directory_vose", "")
        self._dry_run = data.get("dry_run", False)

    def __str__(self) -> str:
        genres_str = ', '.join([genre.name for genre in self._genres]) if self._genres else "Not Set"
        return (
            f"Config::Directory Source <{self._directory_raw}>\n"
            f"Config::Directory Temp <{self._directory_temp}>\n"
            f"Config::Directory Target <{self._directory_vose}>\n"
            f"Config::Dry Run <{self._dry_run}>\n"
            f"Config::Genres <{genres_str}>"
        )

    # ------------------------
    # Setters
    # ------------------------
    def setDirectorySource(self, path: str) -> None:
        if not path:
            raise ValueError("Source directory path cannot be empty.")
        self._directory_raw = path

    def setDirectoryTarget(self, path: str) -> None:
        if not path:
            raise ValueError("Target directory path cannot be empty.")
        self._directory_vose = path

    def setGenres(self, genres: List[GenresEnum]) -> None:
        if not genres or not all(isinstance(genre, GenresEnum) for genre in genres):
            raise ValueError("Genres must be a non-empty list of GenresEnum values.")
        self._genres = genres

    # ------------------------
    # Getters
    # ------------------------
    def getDirectorySource(self) -> str:
        return self._directory_raw

    def getDirectoryTemp(self) -> str:
        return self._directory_temp

    def getDirectoryTarget(self) -> str:
        return self._directory_vose

    def getGenres(self) -> List[str]:
        return [genre.name for genre in self._genres]

    def is_dry_run(self) -> bool:
        """
        Check if dry-run mode is enabled.

        Returns:
            bool: True if dry-run is enabled, False otherwise.
        """
        return self._dry_run
