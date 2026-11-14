"""Compatibility entry point for the Windows filesystem adapter."""
from src.adapters.local_filesystem import LocalFileSystem


class FileSystemWindows(LocalFileSystem):
    """Use the host filesystem with the shared library safety policy."""
