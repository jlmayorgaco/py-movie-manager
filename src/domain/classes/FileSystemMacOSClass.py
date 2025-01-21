import os
import shutil
from typing import List, Optional
from src.domain.interfaces.IFileSystemInterface import IFileSystem


class FileSystemMacOS(IFileSystem):
    """
    FileSystemMacOS: A class to manage filesystem operations on macOS.
    Provides utilities for directory navigation, file operations, and filtering.
    """

    def __init__(self):
        """
        Initialize the FileSystemMacOS with default values.
        """
        self._cwd = os.getcwd()
        self._filter_service = None
        self._config_service = None

    def __str__(self) -> str:
        """
        Return a string representation of the current working directory (CWD).
        """
        return f"FileSystemMacOS::CWD <{self._cwd}>"

    # Directory Navigation Methods
    def cd(self, path: str) -> None:
        """
        Change the current working directory.

        Args:
            path (str): Path to the desired directory.

        Raises:
            ValueError: If the path does not exist.
        """
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
        os.chdir(path)
        self._cwd = os.getcwd()

    def pwd(self) -> str:
        """
        Get the current working directory.

        Returns:
            str: The current working directory.
        """
        return self._cwd

    def back(self, path: str) -> str:
        """
        Move one level up in the directory hierarchy.

        Args:
            path (str): The current directory path.

        Returns:
            str: The parent directory path.
        """
        parent_dir = os.path.dirname(path)
        os.chdir(parent_dir)
        self._cwd = os.getcwd()
        return self._cwd

    # Directory Management Methods
    def mkdir(self, folder_name: str) -> None:
        """
        Create a new directory in the current working directory.

        Args:
            folder_name (str): Name of the folder to create.

        Raises:
            ValueError: If the folder already exists.
        """
        path = os.path.join(self._cwd, folder_name)
        if os.path.exists(path):
            raise ValueError(f"Folder already exists: {folder_name}")
        os.mkdir(path)

    def rmdir(self, folder_name: str) -> None:
        """
        Remove a directory and its contents.

        Args:
            folder_name (str): Name of the folder to remove.

        Raises:
            ValueError: If the folder does not exist.
        """
        path = os.path.join(self._cwd, folder_name)
        if not os.path.exists(path):
            raise ValueError(f"Folder does not exist: {folder_name}")
        shutil.rmtree(path)

    def list_directories(self) -> List[str]:
        """
        List all directories in the current working directory.

        Returns:
            List[str]: A list of directory names.
        """
        return [name for name in os.listdir(self._cwd) if os.path.isdir(os.path.join(self._cwd, name))]

    # File and Folder Operations
    def rename(self, folder: str, new_name: str) -> None:
        """
        Rename a folder in the current directory.

        Args:
            folder (str): The current folder name.
            new_name (str): The new folder name.

        Raises:
            ValueError: If the folder does not exist.
        """
        current_path = os.path.join(self._cwd, folder)
        new_path = os.path.join(self._cwd, new_name)
        if not os.path.exists(current_path):
            raise ValueError(f"Folder does not exist: {folder}")
        os.rename(current_path, new_path)

    def move(self, from_path: str, to_path: str) -> None:
        """
        Move a directory to a new location.

        Args:
            from_path (str): Source directory path.
            to_path (str): Destination directory path.

        Raises:
            ValueError: If the source or destination is invalid.
        """
        abs_from_path = os.path.abspath(from_path)
        abs_to_path = os.path.abspath(to_path)
        if not os.path.exists(abs_from_path):
            raise ValueError(f"Source path does not exist: {abs_from_path}")
        if not os.path.exists(os.path.dirname(abs_to_path)):
            raise ValueError(f"Destination path does not exist: {os.path.dirname(abs_to_path)}")
        shutil.move(abs_from_path, abs_to_path)

    def get_folder(self, folder_name: str) -> str:
        """
        Get the absolute path of a folder.

        Args:
            folder_name (str): Name of the folder.

        Returns:
            str: The absolute path to the folder.
        """
        return os.path.join(self._cwd, folder_name)

    def get_folders(self) -> List[str]:
        """
        List all folders in the current directory.

        Returns:
            List[str]: A list of folder names.
        """
        return self.list_directories()

    def create_folder(self, folder_name: str) -> None:
        """
        Create a single folder.

        Args:
            folder_name (str): Name of the folder to create.
        """
        self.mkdir(folder_name)

    def delete_folder(self, folder_name: str) -> None:
        """
        Delete a single folder.

        Args:
            folder_name (str): Name of the folder to delete.
        """
        self.rmdir(folder_name)

    def create_folders(self, folders: List[str]) -> None:
        """
        Create multiple folders.

        Args:
            folders (List[str]): List of folder names to create.
        """
        for folder in folders:
            self.mkdir(folder)

    def delete_folders(self, folders: List[str]) -> None:
        """
        Delete multiple folders.

        Args:
            folders (List[str]): List of folder names to delete.
        """
        for folder in folders:
            self.rmdir(folder)

    def move_folder(self, origin_path: str, destination_path: str) -> None:
        """
        Move a single folder.

        Args:
            origin_path (str): Source folder path.
            destination_path (str): Destination folder path.
        """
        self.move(origin_path, destination_path)

    def move_folders(self, folders: List[str], destination_path: str) -> None:
        """
        Move multiple folders to a destination.

        Args:
            folders (List[str]): List of folder paths to move.
            destination_path (str): Destination directory.
        """
        for folder in folders:
            self.move(folder, destination_path)

    # Filter and Config Management
    def setFilter(self, filter_service) -> None:
        """
        Set the filter service for the filesystem.
        """
        self._filter_service = filter_service

    def getFilter(self):
        """
        Get the current filter service.
        """
        return self._filter_service

    def hasFilter(self) -> bool:
        """
        Check if a filter service is set.

        Returns:
            bool: True if a filter service is set, False otherwise.
        """
        return self._filter_service is not None

    def setConfig(self, config_service) -> None:
        """
        Set the configuration service for the filesystem.
        """
        self._config_service = config_service

    def getConfig(self):
        """
        Get the current configuration service.
        """
        return self._config_service