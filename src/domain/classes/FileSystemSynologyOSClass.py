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

        self.ensure_directory_exists(abs_destination)

        if self._config_service.is_dry_run():
            print(f"[DRY RUN] Would move contents from {abs_source} to {abs_destination}")
            return

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
    
    def move(self, from_path: str, to_path: str, preserve_folder_name: bool = True) -> None:
        import os
        import shutil

        abs_from = os.path.abspath(from_path)
        abs_to = os.path.abspath(to_path)

        print(f"[MOVE] from: {abs_from}")
        print(f"[MOVE] to:   {abs_to}")

        # ✅ Abort if source doesn't exist
        if not os.path.exists(abs_from):
            raise ValueError(f"❌ Source path does not exist: {abs_from}")

        # Determine destination intelligently
        if preserve_folder_name:
            basename = os.path.basename(abs_from)

            # ⚠️ Fix for nested folder issue:
            # If the folder contains only one subfolder with the same name, skip outer folder
            if os.path.isdir(abs_from):
                items = os.listdir(abs_from)
                if (
                    len(items) == 1
                    and os.path.isdir(os.path.join(abs_from, items[0]))
                    and items[0] == basename
                ):
                    print("[FIX] Detected nested folder structure. Skipping extra folder level.")
                    abs_from = os.path.join(abs_from, items[0])
                    basename = items[0]

            destination = os.path.join(abs_to, basename)
        else:
            destination = abs_to

        print(f"[MOVE] final destination folder: {destination}")

        # ✅ Make sure destination exists
        self.ensure_directory_exists(destination)

        # 🧪 DRY RUN check
        if self._config_service.is_dry_run():
            print(f"[DRY RUN] Would move: {abs_from} → {destination}")
            return

        copied = 0
        skipped = 0

        # ✅ CASE 1 — FROM is a directory
        if os.path.isdir(abs_from):
            print("[INFO] 📁 Source is a directory.")
            print("[INFO] ⚠️ Merge strategy: Existing files are kept, only missing files are copied.")

            for root, _, files in os.walk(abs_from):
                rel_path = os.path.relpath(root, abs_from)
                target_dir = os.path.join(destination, rel_path)

                self.ensure_directory_exists(target_dir)

                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(target_dir, file)

                    if os.path.exists(dest_file):
                        print(f"[SKIP] Already exists: {dest_file}")
                        skipped += 1
                    else:
                        print(f"[COPY] {src_file} → {dest_file}")
                        shutil.copy2(src_file, dest_file)
                        copied += 1

            print(f"[DELETE] Removing source directory after merge: {abs_from}")
            shutil.rmtree(abs_from)

        # ✅ CASE 2 — FROM is a file
        else:
            print("[INFO] 📄 Source is a single file.")
            dest_file = os.path.join(destination, os.path.basename(abs_from))

            if os.path.exists(dest_file):
                print(f"[SKIP] Already exists: {dest_file}")
                skipped += 1
            else:
                print(f"[COPY] {abs_from} → {dest_file}")
                shutil.copy2(abs_from, dest_file)
                os.remove(abs_from)
                copied += 1

        # ✅ Final Summary
        print(f"[SUMMARY] ✅ Copied: {copied}, Skipped: {skipped}")

