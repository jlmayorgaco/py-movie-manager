"""Compatibility entry point for the SynologyOS filesystem adapter."""
from src.adapters.local_filesystem import LocalFileSystem


class FileSystemSynologyOS(LocalFileSystem):
    """Use the host filesystem with the shared library safety policy."""
