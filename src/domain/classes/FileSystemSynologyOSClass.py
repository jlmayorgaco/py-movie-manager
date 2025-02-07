import os
import shutil
from typing import List, Optional
from src.domain.interfaces.IFileSystemInterface import IFileSystem


class FileSystemSynologyOS(IFileSystem):
    """
    FileSystemSynologyOS: A class to manage filesystem operations on Synology NAS.
    Provides utilities for directory navigation, file operations, and filtering.
    """

    def __init__(self):
        """
        Initialize the FileSystemSynologyOS with default values.
        """
        self._cwd = os.getcwd()
        self._filter_service = None
        self._config_service = None

    def __str__(self) -> str:
        """Return a string representation of the current working directory (CWD)."""
        return f"FileSystemSynologyOS::CWD <{self._cwd}>"

    # ✅ Ensure directory exists
    def ensure_directory_exists(self, path: str) -> None:
        """Ensure a directory exists; if not, create it."""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # ✅ Implement Abstract Methods for `cd` and `back`
    def cd(self, path: str) -> None:
        """Change the current working directory."""
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
        os.chdir(path)
        self._cwd = os.getcwd()

    def back(self) -> str:
        """Move one level up in the directory hierarchy."""
        parent_dir = os.path.dirname(self._cwd)
        os.chdir(parent_dir)
        self._cwd = os.getcwd()
        return self._cwd

    # ✅ Directory Management
    def pwd(self) -> str:
        """Get the current working directory."""
        return self._cwd

    def mkdir(self, folder_name: str) -> None:
        """Create a new directory in the current working directory."""
        path = os.path.join(self._cwd, folder_name)
        if os.path.exists(path):
            return  
        self.ensure_directory_exists(path)

    def rmdir(self, folder_name: str) -> None:
        """Remove a directory and its contents."""
        path = os.path.join(self._cwd, folder_name)
        if not os.path.exists(path):
            raise ValueError(f"Folder does not exist: {folder_name}")
        shutil.rmtree(path)

    def list_directories(self) -> List[str]:
        """List all directories in the current working directory."""
        return [name for name in os.listdir(self._cwd) if os.path.isdir(os.path.join(self._cwd, name))]

    # ✅ Implement Abstract Methods from `IFileSystem`
    def create_folder(self, folder_name: str) -> None:
        """Create a single folder."""
        self.mkdir(folder_name)

    def create_folders(self, folders: List[str]) -> None:
        """Create multiple folders."""
        for folder in folders:
            self.mkdir(folder)

    def delete_folder(self, folder_name: str) -> None:
        """Delete a single folder."""
        self.rmdir(folder_name)

    def delete_folders(self, folders: List[str]) -> None:
        """Delete multiple folders."""
        for folder in folders:
            self.rmdir(folder)

    def get_folder(self, folder_name: str) -> str:
        """Get the absolute path of a folder."""
        return os.path.join(self._cwd, folder_name)

    def get_folders(self) -> List[str]:
        """List all folders in the current directory."""
        return self.list_directories()

    def move_folder(self, origin_path: str, destination_path: str) -> None:
        """Move a single folder."""
        self.move(origin_path, destination_path)

    def move_folders(self, folders: List[str], destination_path: str) -> None:
        """Move multiple folders to a destination."""
        for folder in folders:
            self.move(folder, destination_path)

    def move(self, from_path: str, to_path: str) -> None:
        """Move a file or directory to a new location."""
        abs_from_path = os.path.abspath(from_path)
        abs_to_path = os.path.abspath(to_path)

        if not os.path.exists(abs_from_path):
            raise ValueError(f"Source path does not exist: {abs_from_path}")

        self.ensure_directory_exists(abs_to_path)
        destination = os.path.join(abs_to_path, os.path.basename(abs_from_path))

        if os.path.isdir(abs_from_path):
            if not os.path.exists(destination):
                shutil.copytree(abs_from_path, destination)
            else:
                for root, _, files in os.walk(abs_from_path):
                    target_dir = os.path.join(destination, os.path.relpath(root, abs_from_path))
                    self.ensure_directory_exists(target_dir)
                    for file in files:
                        shutil.copy2(os.path.join(root, file), os.path.join(target_dir, file))
            shutil.rmtree(abs_from_path)
        else:
            shutil.copy2(abs_from_path, destination)
            os.remove(abs_from_path)

    def join(self, *paths) -> str:
        """Join multiple path components intelligently."""
        return os.path.join(*paths)

    def deep_tree_move(self, source: str, destination: str) -> None:
        """Perform a deep tree move from source to destination."""
        abs_source = os.path.abspath(source)
        abs_destination = os.path.abspath(destination)

        if not os.path.exists(abs_source):
            raise ValueError(f"Source directory does not exist: {abs_source}")

        self.ensure_directory_exists(abs_destination)

        for item in os.listdir(abs_source):
            src_item = os.path.join(abs_source, item)
            dest_item = os.path.join(abs_destination, item)

            if os.path.isdir(src_item):
                if os.path.exists(dest_item) and os.path.isdir(dest_item):
                    for root, _, files in os.walk(src_item):
                        target_dir = os.path.join(dest_item, os.path.relpath(root, src_item))
                        self.ensure_directory_exists(target_dir)
                        for file in files:
                            shutil.copy2(os.path.join(root, file), os.path.join(target_dir, file))
                else:
                    shutil.copytree(src_item, dest_item)
            else:
                shutil.copy2(src_item, dest_item)

        shutil.rmtree(abs_source)

    # ✅ Filter and Config Management
    def setFilter(self, filter_service) -> None:
        """Set the filter service for the filesystem."""
        self._filter_service = filter_service

    def getFilter(self):
        """Get the current filter service."""
        return self._filter_service

    def hasFilter(self) -> bool:
        """Check if a filter service is set."""
        return self._filter_service is not None

    def setConfig(self, config_service) -> None:
        """Set the configuration service for the filesystem."""
        self._config_service = config_service

    def getConfig(self):
        """Get the current configuration service."""
        return self._config_service
    
    def get_folders_at(self, path: str) -> List[str]:
        """
        Get all folders at a specific directory.

        Args:
            path (str): The directory path to scan.

        Returns:
            List[str]: A list of folder names.
        """
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")

        return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

    def rename(self, old_path: str, new_path: str) -> None:
        """
        Rename a file or folder.

        Args:
            old_path (str): The current file or folder name (absolute path).
            new_path (str): The new file or folder name (absolute path).

        Raises:
            ValueError: If the original file/folder does not exist.
            OSError: If renaming fails.
        """
        if not os.path.exists(old_path):
            raise ValueError(f"Cannot rename: Source path does not exist: {old_path}")

        if os.path.exists(new_path):
            raise ValueError(f"Cannot rename: Target path already exists: {new_path}")

        try:
            os.rename(old_path, new_path)
        except OSError as e:
            raise OSError(f"Failed to rename '{old_path}' to '{new_path}': {e}")
