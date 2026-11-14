"""Shared rules for reserved directories and movie-name metadata."""

import hashlib
import re
import unicodedata

GENRE_TAG = re.compile(r"\[g-([^\]]*)\]", re.IGNORECASE)
DIRECTOR_TAG = re.compile(r"\[d-([^\]]*)\]", re.IGNORECASE)
METADATA_TAG = re.compile(r"\[[gd]-[^\]]*\]", re.IGNORECASE)
TRANSFER_PREFIX = ".pymovie-transfer-"
LOCK_NAME = ".pymovie-manager.lock"
SYSTEM_NAMES = {"@eadir", "#recycle", "@recycle", ".deletedbytmm", LOCK_NAME}
WINDOWS_RESERVED = re.compile(
    r"^(?:con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³]|conin\$|conout\$)(?:\.|$)", re.I
)
VIDEO_SUFFIXES = {
    ".mkv",
    ".mp4",
    ".avi",
    ".m4v",
    ".mov",
    ".iso",
    ".mpg",
    ".mpeg",
    ".wmv",
    ".webm",
    ".ts",
}


def name_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def staging_name(destination_name: str) -> str:
    # Stable even on case-insensitive filesystems, so retries do not pile up copies.
    key = name_key(destination_name).encode("utf-8", errors="surrogatepass")
    return TRANSFER_PREFIX + hashlib.sha256(key).hexdigest()[:24]


def reserved(name: str) -> bool:
    normalized = name_key(name)
    return normalized in SYSTEM_NAMES or normalized.startswith(TRANSFER_PREFIX)


def valid_movie_name(name: str, *, windows: bool) -> bool:
    if name in {"", ".", ".."} or reserved(name) or "/" in name or "\x00" in name:
        return False
    return not windows or (
        not name.endswith((".", " "))
        and not any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name)
        and not WINDOWS_RESERVED.match(name)
    )


def tag(pattern: re.Pattern, name: str) -> str:
    match = pattern.search(name)
    value = match[1].strip() if match else ""
    return "" if value.casefold() == "unknown" else value


def clean_name(name: str) -> str:
    return " ".join(METADATA_TAG.sub("", name).split())
