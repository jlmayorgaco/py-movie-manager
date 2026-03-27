import os
import shutil
from typing import List

from src.domain.interfaces.IFileSystemInterface import IFileSystem


class FileSystemWindows(IFileSystem):
    """
    FileSystemWindows: filesystem adapter for Windows.

    Designed to work with:
    - Local paths: C:\\Media\\...
    - Mapped drives: Z:\\Movies\\...
    - SMB / UNC shares: \\\\NAS\\Media\\...

    Semantics:
    - move(from_path, to_path) treats `to_path` as the FINAL destination path.
    """

    def __init__(self) -> None:
        self._cwd = os.getcwd()
        self._filter_service = None
        self._config_service = None

    def __str__(self) -> str:
        return f"FileSystemWindows::CWD <{self._cwd}>"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalize_path(self, path: str) -> str:
        if not path or not str(path).strip():
            raise ValueError("Path cannot be empty")
        return os.path.normpath(str(path).strip())

    def _abs_path(self, path: str) -> str:
        normalized = self._normalize_path(path)
        if os.path.isabs(normalized):
            return normalized
        return os.path.abspath(normalized)

    def _require_exists(self, path: str) -> str:
        abs_path = self._abs_path(path)
        if not os.path.exists(abs_path):
            raise ValueError(f"Path does not exist: {abs_path}")
        return abs_path

    def _require_dir(self, path: str) -> str:
        abs_path = self._require_exists(path)
        if not os.path.isdir(abs_path):
            raise ValueError(f"Directory does not exist: {abs_path}")
        return abs_path

    def _ensure_parent_exists(self, path: str) -> None:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _copy_file_streaming(self, src: str, dst: str) -> None:
        self._ensure_parent_exists(dst)
        shutil.copy2(src, dst)

    def _iter_dir_entries(self, path: str):
        abs_path = self._require_dir(path)
        with os.scandir(abs_path) as entries:
            for entry in entries:
                yield entry

    def _merge_directories(self, src_dir: str, dst_dir: str) -> None:
        src_dir = self._require_dir(src_dir)
        dst_dir = self._abs_path(dst_dir)
        os.makedirs(dst_dir, exist_ok=True)

        for root, dirs, files in os.walk(src_dir):
            rel_root = os.path.relpath(root, src_dir)
            target_root = dst_dir if rel_root == "." else os.path.join(dst_dir, rel_root)
            os.makedirs(target_root, exist_ok=True)

            for dir_name in dirs:
                os.makedirs(os.path.join(target_root, dir_name), exist_ok=True)

            for file_name in files:
                src_file = os.path.join(root, file_name)
                dst_file = os.path.join(target_root, file_name)
                self._copy_file_streaming(src_file, dst_file)

    # ------------------------------------------------------------------
    # Basic filesystem API
    # ------------------------------------------------------------------
    def ensure_directory_exists(self, path: str) -> None:
        os.makedirs(self._abs_path(path), exist_ok=True)

    def exists(self, path: str) -> bool:
        return os.path.exists(self._abs_path(path))

    def is_file(self, path: str) -> bool:
        return os.path.isfile(self._abs_path(path))

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(self._abs_path(path))

    def get_size(self, path: str) -> int:
        return os.path.getsize(self._require_exists(path))

    def copy_file(self, src: str, dst: str) -> None:
        self._copy_file_streaming(self._require_exists(src), self._abs_path(dst))

    def remove_file(self, path: str) -> None:
        os.remove(self._require_exists(path))

    def remove_directory(self, path: str) -> None:
        shutil.rmtree(self._require_dir(path))

    def cd(self, path: str) -> None:
        abs_path = self._require_dir(path)
        os.chdir(abs_path)
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
        os.makedirs(path, exist_ok=True)

    def rmdir(self, folder_name: str) -> None:
        path = os.path.join(self._cwd, folder_name)
        if not os.path.exists(path):
            raise ValueError(f"Folder does not exist: {folder_name}")
        shutil.rmtree(path)

    def list_directories(self) -> List[str]:
        result: List[str] = []
        with os.scandir(self._cwd) as entries:
            for entry in entries:
                if entry.is_dir():
                    result.append(entry.name)
        return sorted(result)

    # ------------------------------------------------------------------
    # Interface compatibility helpers
    # ------------------------------------------------------------------
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
        abs_destination = self._abs_path(destination_path)
        for folder in folders:
            folder_name = os.path.basename(self._abs_path(folder))
            final_destination = os.path.join(abs_destination, folder_name)
            self.move(folder, final_destination)

    def move(self, from_path: str, to_path: str) -> None:
        """
        Move a file or directory to its FINAL destination path.
        """
        abs_from_path = self._require_exists(from_path)
        abs_to_path = self._abs_path(to_path)

        if abs_from_path == abs_to_path:
            return

        self._ensure_parent_exists(abs_to_path)

        try:
            shutil.move(abs_from_path, abs_to_path)
            return
        except Exception:
            pass

        if os.path.isdir(abs_from_path):
            if os.path.exists(abs_to_path):
                if not os.path.isdir(abs_to_path):
                    raise ValueError(
                        f"Cannot merge directory into file destination: {abs_to_path}"
                    )
                self._merge_directories(abs_from_path, abs_to_path)
                shutil.rmtree(abs_from_path)
            else:
                shutil.copytree(abs_from_path, abs_to_path)
                shutil.rmtree(abs_from_path)
        else:
            if os.path.isdir(abs_to_path):
                abs_to_path = os.path.join(abs_to_path, os.path.basename(abs_from_path))
            self._copy_file_streaming(abs_from_path, abs_to_path)
            os.remove(abs_from_path)

    def join(self, *paths: str) -> str:
        return os.path.join(*paths)

    def deep_tree_move(self, source: str, destination: str) -> None:
        abs_source = self._require_dir(source)
        abs_destination = self._abs_path(destination)

        os.makedirs(abs_destination, exist_ok=True)

        with os.scandir(abs_source) as entries:
            for entry in entries:
                src_item = entry.path
                dst_item = os.path.join(abs_destination, entry.name)

                if entry.is_dir():
                    if os.path.exists(dst_item) and os.path.isdir(dst_item):
                        self._merge_directories(src_item, dst_item)
                        shutil.rmtree(src_item)
                    else:
                        shutil.move(src_item, dst_item)
                else:
                    self._copy_file_streaming(src_item, dst_item)
                    os.remove(src_item)

        shutil.rmtree(abs_source)

    # ------------------------------------------------------------------
    # Filter / config management
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Directory inspection helpers
    # ------------------------------------------------------------------
    def get_folders_at(self, path: str) -> List[str]:
        result: List[str] = []
        for entry in self._iter_dir_entries(path):
            if entry.is_dir():
                result.append(entry.name)
        return sorted(result)

    def get_files_at(self, path: str) -> List[str]:
        result: List[str] = []
        for entry in self._iter_dir_entries(path):
            if entry.is_file():
                result.append(entry.name)
        return sorted(result)

    def rename(self, old_path: str, new_path: str) -> None:
        abs_old_path = self._require_exists(old_path)
        abs_new_path = self._abs_path(new_path)

        if os.path.exists(abs_new_path):
            raise ValueError(
                f"Cannot rename: Target path already exists: {abs_new_path}"
            )

        self._ensure_parent_exists(abs_new_path)

        try:
            os.rename(abs_old_path, abs_new_path)
        except OSError as exc:
            raise OSError(
                f"Failed to rename '{abs_old_path}' to '{abs_new_path}': {exc}"
            ) from exc