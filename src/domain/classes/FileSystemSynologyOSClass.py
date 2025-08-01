import os
import re
import shutil
from typing import List, Optional
from src.domain.interfaces.IFileSystemInterface import IFileSystem


class FileSystemSynologyOS(IFileSystem):
    """
    FileSystemSynologyOS: A Linux-compatible class for managing file operations
    on Synology NAS. All operations respect dry_run mode for safe testing.
    """

    def __init__(self):
        self._cwd = os.getcwd()
        self._filter_service = None
        self._config_service = None

    def __str__(self) -> str:
        return f"FileSystemSynologyOS::CWD <{self._cwd}>"

    def ensure_directory_exists(self, path: str) -> None:
        if not os.path.exists(path):
            if self._config_service.is_dry_run():
                print(f"[DRY RUN] Would create directory: {path}")
            else:
                os.makedirs(path, exist_ok=True)

    def cd(self, path: str) -> None:
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
        os.chdir(path)
        self._cwd = os.getcwd()

    def back(self) -> str:
        parent_dir = os.path.dirname(self._cwd)
        os.chdir(parent_dir)
        self._cwd = os.getcwd()
        return self._cwd

    def pwd(self) -> str:
        return self._cwd

    def mkdir(self, folder_name: str) -> None:
        path = os.path.join(self._cwd, folder_name)
        self.ensure_directory_exists(path)

    def rmdir(self, folder_name: str) -> None:
        path = os.path.join(self._cwd, folder_name)
        if os.path.exists(path):
            if self._config_service.is_dry_run():
                print(f"[DRY RUN] Would remove directory: {path}")
            else:
                shutil.rmtree(path)
        else:
            raise ValueError(f"Folder does not exist: {folder_name}")

    def list_directories(self) -> List[str]:
        return [name for name in os.listdir(self._cwd) if os.path.isdir(os.path.join(self._cwd, name))]

    def create_folder(self, folder_name: str) -> None:
        self.mkdir(folder_name)

    def create_folders(self, folders: List[str]) -> None:
        for folder in folders:
            self.mkdir(folder)

    def delete_folder(self, folder_name: str) -> None:
        self.rmdir(folder_name)

    def delete_folders(self, folders: List[str]) -> None:
        for folder in folders:
            self.rmdir(folder)

    def get_folder(self, folder_name: str) -> str:
        return os.path.join(self._cwd, folder_name)

    def get_folders(self) -> List[str]:
        return self.list_directories()

    def move_folder(self, origin_path: str, destination_path: str) -> None:
        self.move(origin_path, destination_path)

    def move_folders(self, folders: List[str], destination_path: str) -> None:
        for folder in folders:
            self.move(folder, destination_path)

    def join(self, *paths) -> str:
        return os.path.join(*paths)

    def deep_tree_move(self, source: str, destination: str) -> None:
        abs_source = os.path.abspath(source)
        abs_destination = os.path.abspath(destination)

        if not os.path.exists(abs_source):
            raise ValueError(f"Source directory does not exist: {abs_source}")

        if self._config_service.is_dry_run():
            print(f"[DRY RUN] Would move {abs_source} → {abs_destination}")
            return

        try:
            os.rename(abs_source, abs_destination)
        except OSError as e:
            if e.errno == 18:  # Cross-device link
                print("Cross-device detected. Falling back to copy + delete strategy.")
                self.ensure_directory_exists(abs_destination)
                for item in os.listdir(abs_source):
                    src_item = os.path.join(abs_source, item)
                    dest_item = os.path.join(abs_destination, item)
                    if os.path.isdir(src_item):
                        shutil.copytree(src_item, dest_item)
                    else:
                        shutil.copy2(src_item, dest_item)
                shutil.rmtree(abs_source)
            else:
                raise RuntimeError(f"Failed to move directory: {e}")


    def rename(self, old_path: str, new_path: str) -> None:
        if not os.path.exists(old_path):
            raise ValueError(f"Cannot rename: Source path does not exist: {old_path}")
        if os.path.exists(new_path):
            raise ValueError(f"Cannot rename: Target path already exists: {new_path}")

        if self._config_service.is_dry_run():
            print(f"[DRY RUN] Would rename: {old_path} → {new_path}")
        else:
            os.rename(old_path, new_path)

    def get_folders_at(self, path: str) -> List[str]:
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
        return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

    def setFilter(self, filter_service) -> None:
        self._filter_service = filter_service

    def getFilter(self):
        return self._filter_service

    def hasFilter(self) -> bool:
        return self._filter_service is not None

    def setConfig(self, config_service) -> None:
        self._config_service = config_service

    def getConfig(self):
        return self._config_service
    
    def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists at the given path.
        """
        return os.path.exists(path)
        
    def move(self, from_path: str, to_path: str) -> None:
        """
        Move a directory or file to a new location.
        If `from_path` is a folder and `to_path` is the desired final folder name, move contents there.
        """
        if os.path.isdir(from_path):
            # Ensure parent of `to_path` exists
            os.makedirs(os.path.dirname(to_path), exist_ok=True)

            # Move the whole folder (rename)
            shutil.move(from_path, to_path)
        else:
            # It's a file — ensure destination directory exists
            os.makedirs(os.path.dirname(to_path), exist_ok=True)
            shutil.move(from_path, to_path)
