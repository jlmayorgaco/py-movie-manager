import json
import os

import pytest

from conftest import SYNOLOGY_MOVIE_FILES, make_movie, snapshot, symlink
from main import main
from src.adapters import local_filesystem
from src.domain.classes.FileSystemSynologyOSClass import FileSystemSynologyOS


def run_cli(config, *args):
    return main(["--os", "synology", "--config", str(config), *args])


def test_nested_metadata_is_planned_and_transferred_intact(library):
    config, raw, temp, vose = library
    source = make_movie(raw / "[g-Bélica] Película (2001)", SYNOLOGY_MOVIE_FILES)
    (source / "extrathumbs/@eaDir/empty").mkdir()
    (raw / "@eaDir").mkdir()
    (raw / "@eaDir/root-info").write_bytes(b"keep in RAW")
    before = snapshot(raw, temp, vose)
    expected_tree = {
        path.relative_to(source): value for path, value in snapshot(source).items()
    }
    report = config.with_name("plan.json")

    assert run_cli(config, "--dry-run", "--report", str(report)) == 0
    assert snapshot(raw, temp, vose) == before
    plan = json.loads(report.read_text(encoding="utf-8"))
    assert plan["counts"] == {"planned": 3}
    expected = vose / "WAR" / "Película (2001)"
    assert plan["operations"][-1]["destination"] == str(expected)

    assert run_cli(config, "--apply") == 0
    assert not source.exists()
    assert {
        path.relative_to(expected): value for path, value in snapshot(expected).items()
    } == expected_tree
    assert (raw / "@eaDir/root-info").read_bytes() == b"keep in RAW"
    assert not (vose / "MUSIC").exists()
    after = snapshot(raw, temp, vose)
    assert run_cli(config, "--apply") == 0
    assert snapshot(raw, temp, vose) == after


def test_synology_metadata_does_not_bypass_destination_conflicts(library):
    config, raw, temp, vose = library
    source = make_movie(raw / "[g-Bélica] Film", SYNOLOGY_MOVIE_FILES)
    destination = make_movie(vose / "WAR/Film", SYNOLOGY_MOVIE_FILES)
    (destination / ".actors/@eaDir/meta").write_bytes(b"different metadata")
    before = snapshot(raw, temp, vose)
    report = config.with_name("conflicts.json")

    assert run_cli(config, "--apply", "--report", str(report)) == 2
    assert snapshot(raw, temp, vose) == before
    result = json.loads(report.read_text(encoding="utf-8"))
    (conflict,) = result["operations"]
    assert conflict["status"] == "conflict"
    assert conflict["reason"] == "same_name_different_content"
    assert conflict["source"] == str(source)
    assert conflict["destination"] == str(destination)


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        (
            ".actors/@eaDir",
            "reserved_entry_inside_movie",
        ),  # A regular file, not a directory.
        (".actors/@eaDir/#recycle/file", "reserved_entry_inside_movie"),
        (".actors/@eaDir/@Recycle/file", "reserved_entry_inside_movie"),
        (".actors/@eaDir/.deletedByTMM/file", "reserved_entry_inside_movie"),
        (".actors/@eaDir/.pymovie-manager.lock", "reserved_entry_inside_movie"),
        (
            ".actors/@eaDir/.pymovie-transfer-abcd/payload",
            "reserved_entry_inside_movie",
        ),
        (".actors/@eaDir/AlreadyCopied_thumb", "legacy_partial_transfer_marker"),
    ],
)
def test_reserved_entries_still_block_planning_and_transfer(library, name, reason):
    config, raw, temp, vose = library
    movie = make_movie(raw / "[g-War] Film", {"film.mkv": b"feature", name: b"keep"})
    before = snapshot(raw, temp, vose)
    report = config.with_name("blocked.json")

    assert run_cli(config, "--apply", "--report", str(report)) == 2
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["counts"] == {"conflict": 1}
    assert result["operations"][0]["reason"] == reason
    adapter = FileSystemSynologyOS(apply=True, roots=(raw, vose))
    with pytest.raises(ValueError, match=reason):
        adapter.transfer(movie, vose / "Film")
    assert snapshot(raw, temp, vose) == before


@pytest.mark.parametrize(
    "bad_entry", ["metadata_link", "link_inside_metadata", "bind_mount", "fifo"]
)
def test_metadata_never_bypasses_link_mount_or_special_file_checks(
    library, monkeypatch, bad_entry
):
    config, raw, temp, vose = library
    movie = make_movie(raw / "[g-War] Film")
    outside = make_movie(config.parent / "outside")
    metadata = movie / ".actors/@eaDir"
    metadata.parent.mkdir()
    if bad_entry == "metadata_link":
        symlink(metadata, outside)
    else:
        metadata.mkdir()
        if bad_entry == "link_inside_metadata":
            symlink(metadata / "link", outside)
        elif bad_entry == "bind_mount":
            # The mount uses the same device/inode rules as an ordinary directory.
            # Linux identifies the boundary through mountinfo, even with spaces.
            mounted = metadata / "Mounted metadata"
            mounted.mkdir()
            mountinfo = config.with_name("mountinfo")
            escaped = (
                os.fsencode(mounted).replace(b"\\", rb"\134").replace(b" ", rb"\040")
            )
            mountinfo.write_bytes(
                b"36 35 98:0 /origin " + escaped + b" rw - ext4 /dev/x rw\n"
            )
            monkeypatch.setattr(
                local_filesystem,
                "_mount_points",
                lambda: local_filesystem._read_mount_points(mountinfo),
            )
        else:
            if not hasattr(os, "mkfifo"):
                pytest.skip("requires a POSIX FIFO")
            os.mkfifo(metadata / "pipe")
    before = snapshot(raw, temp, vose, outside)

    assert run_cli(config, "--apply") == 2
    adapter = FileSystemSynologyOS(apply=True, roots=(raw, vose))
    with pytest.raises(
        ValueError, match="Cannot transfer a link, special file or nested mount"
    ):
        adapter.transfer(movie, vose / "Film")
    assert snapshot(raw, temp, vose, outside) == before
