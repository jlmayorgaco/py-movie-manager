import json

import pytest


@pytest.fixture
def library(tmp_path):
    base = tmp_path.resolve()
    raw, temp, vose = (base / name for name in ("RAW", "TEMP", "VOSE"))
    raw.mkdir()
    vose.mkdir()
    config = base / "local.json"
    config.write_text(
        json.dumps(
            {
                "directory_raw": str(raw),
                "directory_temp": str(temp),
                "directory_vose": str(vose),
                "dry_run": False,
            }
        ),
        encoding="utf-8",
    )
    return config, raw, temp, vose


def make_movie(folder, files=None):
    if files is None:
        files = {
            "movie.mkv": b"feature",
            "es.srt": b"subtitle",
            "extras/poster.jpg": b"image",
        }
    folder.mkdir(parents=True)
    for name, data in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return folder


def snapshot(*roots):
    state = {}
    for root in roots:
        state[root] = "dir" if root.is_dir() else None
        for path in root.rglob("*"):
            if path.is_symlink():
                state[path] = ("link", str(path.readlink()))
            elif path.is_file():
                state[path] = ("file", path.read_bytes(), path.stat().st_mtime_ns)
            else:
                state[path] = "dir"
    return state
