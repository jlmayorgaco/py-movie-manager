"""Compatibility entry point for the MacOS filesystem adapter."""
from src.adapters.local_filesystem import LocalFileSystem


class FileSystemMacOS(LocalFileSystem):
    """Use the host filesystem with the shared library safety policy."""
