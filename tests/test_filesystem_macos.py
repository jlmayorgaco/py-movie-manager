import errno
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from conftest import make_movie, snapshot
from src.adapters import local_filesystem
from src.adapters.native_rename import rename_noreplace
from src.domain.classes.ConfigClass import Config
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS
from src.domain.classes.FileSystemSynologyOSClass import FileSystemSynologyOS
from src.domain.classes.FileSystemWindowsClass import FileSystemWindows


@pytest.mark.parametrize(
    "adapter", [FileSystemMacOS, FileSystemSynologyOS, FileSystemWindows]
)
def test_all_adapters_honor_dry_run_for_all_mutations(library, adapter):
    config_file, raw, temp, vose = library
    config = Config(str(config_file))
    config.set_dry_run(True)
    fs = adapter(apply=True, roots=(raw, temp, vose))
    fs.setConfig(config)
    source = make_movie(raw / "movie")
    dest = vose / "movie"
    before = snapshot(raw, temp, vose)
    fs.move(str(source), str(dest))
    fs.rename(str(source), str(dest))
    fs.deep_tree_move(str(source), str(dest))
    fs.ensure_directory_exists(str(temp))
    fs.remove_file(str(source / "movie.mkv"))
    fs.remove_directory(str(source))
    fs.copy_file(str(source / "movie.mkv"), str(vose / "x.mkv"))
    assert snapshot(raw, temp, vose) == before


def test_apply_adapter_cannot_move_outside_roots_into_descendant_or_erase_tree(library):
    config, raw, temp, vose = library
    fs = FileSystemSynologyOS(apply=True, roots=(raw, temp, vose))
    movie = make_movie(raw / "movie")
    before = snapshot(raw, temp, vose)
    for target in (movie / "child", config.parent / "outside", movie, vose):
        with pytest.raises(ValueError):
            fs.transfer(movie, target)
    with pytest.raises(OSError):
        fs.remove_directory(str(movie))
    assert snapshot(raw, temp, vose) == before


def test_native_rename_never_replaces_even_empty_directory(library):
    _, raw, _, vose = library
    src = make_movie(raw / "movie")
    dst = vose / "movie"
    dst.mkdir()
    with pytest.raises(OSError):
        rename_noreplace(src, dst)
    assert (src / "movie.mkv").is_file()
    assert not list(dst.iterdir())


@pytest.fixture
def cross_device(library, monkeypatch):
    _, raw, _, vose = library
    fs = FileSystemSynologyOS(apply=True, roots=(raw, vose))
    source = make_movie(raw / "movie")
    dest = vose / "movie"

    def rename(src, dst):
        if src == source:
            raise OSError(errno.EXDEV, "simulated cross-device move")
        rename_noreplace(src, dst)

    monkeypatch.setattr(local_filesystem, "rename_noreplace", rename)
    return fs, source, dest


def test_cross_device_verifies_publishes_then_removes_source(cross_device):
    fs, source, dest = cross_device
    (source / "empty").mkdir()
    fs.transfer(source, dest)
    assert not source.exists()
    assert (dest / "movie.mkv").read_bytes() == b"feature"
    assert (dest / "es.srt").read_bytes() == b"subtitle"
    assert (dest / "empty").is_dir()
    assert list(dest.parent.iterdir()) == [dest]


@pytest.mark.parametrize("failure", ["space", "corruption", "publish_race"])
def test_cross_device_failures_leave_source_and_no_partial_final(
    cross_device, monkeypatch, failure
):
    fs, source, dest = cross_device
    before = snapshot(source)
    copy = local_filesystem.shutil.copyfile
    original_rename = local_filesystem.rename_noreplace

    def fail_copy(src, dst, **kwargs):
        copy(src, dst, **kwargs)
        if src.name == "movie.mkv":
            if failure == "space":
                raise OSError(errno.ENOSPC, "synthetic disk full")
            dst.write_bytes(b"broken")  # same size, different bytes

    def competing_publish(src, dst):
        if src != source:
            dst.mkdir()
            (dst / "other.mkv").write_bytes(b"other job")
        original_rename(src, dst)

    if failure == "publish_race":
        monkeypatch.setattr(local_filesystem, "rename_noreplace", competing_publish)
    else:
        monkeypatch.setattr(local_filesystem.shutil, "copyfile", fail_copy)
    with pytest.raises(OSError, match="inspect staging"):
        fs.transfer(source, dest)
    assert snapshot(source) == before
    if failure == "publish_race":
        assert list(dest.iterdir()) == [dest / "other.mkv"]
    else:
        assert not dest.exists()
    staging = list(dest.parent.glob(".pymovie-transfer-*"))
    assert len(staging) == 1
    if failure != "publish_race":
        with pytest.raises(FileExistsError, match="staging needs review"):
            fs.transfer(source, dest)
        assert list(dest.parent.glob(".pymovie-transfer-*")) == staging


def test_cleanup_failure_leaves_a_complete_final_copy(cross_device, monkeypatch):
    fs, source, dest = cross_device
    unlink = type(source).unlink

    def fail_unlink(path, *args, **kwargs):
        if path == source / "es.srt":
            raise PermissionError("synthetic source cleanup failure")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(source), "unlink", fail_unlink)
    with pytest.raises(OSError, match="cleanup"):
        fs.transfer(source, dest)
    assert (source / "es.srt").is_file()
    assert (dest / "movie.mkv").read_bytes() == b"feature"
    assert (dest / "es.srt").read_bytes() == b"subtitle"
    assert (dest / "extras/poster.jpg").read_bytes() == b"image"


def test_cross_device_hard_links_are_preserved(cross_device):
    fs, source, dest = cross_device
    os.link(source / "movie.mkv", source / "linked.mkv")
    before = snapshot(source)
    with pytest.raises(ValueError, match="cannot preserve hard links"):
        fs.transfer(source, dest)
    assert snapshot(source) == before
    assert not list(dest.parent.iterdir())


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux tmpfs")
def test_real_cross_device_transfer(library):
    _, raw, _, _ = library
    shared_memory = Path("/dev/shm")
    if not shared_memory.is_dir() or shared_memory.stat().st_dev == raw.stat().st_dev:
        pytest.skip("no separate tmpfs volume")
    with TemporaryDirectory(prefix="pymovie-test-", dir=shared_memory) as temporary:
        target = Path(temporary)
        fs = FileSystemSynologyOS(apply=True, roots=(raw, target))
        source = make_movie(raw / "movie")
        destination = target / "movie"
        fs.transfer(source, destination)
        assert not source.exists()
        assert (destination / "movie.mkv").read_bytes() == b"feature"
        assert (destination / "es.srt").read_bytes() == b"subtitle"
        assert list(target.iterdir()) == [destination]
