import errno
import json

import pytest

from conftest import make_movie, snapshot
from main import main
from src.adapters import local_filesystem


@pytest.mark.parametrize("options", [[], ["--dry-run"], ["--plan"]])
def test_default_and_explicit_dry_run_plan_all_stages(library, options):
    config, raw, temp, vose = library
    name = "[g-Drama][d-黒澤 明] Película 日本 [Extended Cut] (2001)"
    movie = make_movie(raw / name)
    before = snapshot(raw, temp, vose)
    report = config.with_name("plan.json")
    assert (
        main(
            [
                "--os",
                "synology",
                "--config",
                str(config),
                "--report",
                str(report),
                *options,
            ]
        )
        == 0
    )
    assert snapshot(raw, temp, vose) == before
    plan = json.loads(report.read_text(encoding="utf-8"))
    assert plan["mode"] == "dry-run"
    assert plan["counts"] == {"planned": 3}
    first, rename, last = plan["operations"]
    assert [step["stage"] for step in (first, rename, last)] == [
        "raw_to_temp",
        "rename_in_temp",
        "temp_to_vose",
    ]
    assert first["source"] == str(movie)
    assert first["destination"] == rename["source"]
    assert rename["destination"] == last["source"]
    assert last["destination"] == str(
        vose / "DRAMA" / "Película 日本 [Extended Cut] (2001)"
    )


def test_apply_several_genres_editions_and_companion_files(library):
    config, raw, temp, vose = library
    (vose / "Drama").mkdir()
    names = [
        "[g-Drama] Le Film (2005) [Extended Cut]",
        "[g-Drama] Le Film (2005) [Theatrical Cut]",
        "[g-Science Fiction] 한국 (2011)",
    ]
    for name in names:
        make_movie(raw / name)
    empty = make_movie(raw / "[g-Drama] Empty", {})
    untagged = make_movie(raw / "Untagged")
    args = ["--os", "synology", "--config", str(config), "--apply"]
    assert main(args) == 0
    assert set(path.name for path in raw.iterdir()) == {empty.name, untagged.name}
    first = vose / "Drama" / "Le Film (2005) [Extended Cut]"
    assert (first / "es.srt").read_bytes() == b"subtitle"
    assert (first / "extras/poster.jpg").read_bytes() == b"image"
    assert (vose / "Drama/Le Film (2005) [Theatrical Cut]/movie.mkv").is_file()
    assert (vose / "SCIENCE_FICTION/한국 (2011)/movie.mkv").is_file()
    after = snapshot(raw, temp, vose)
    assert main(args) == 0
    assert snapshot(raw, temp, vose) == after


@pytest.mark.parametrize(
    ("destination_files", "reason"),
    [
        ({"movie.mkv": b"aaa", "es.srt": b"s"}, "identical_tree_preserved"),
        ({"movie.mkv": b"bbb", "es.srt": b"s"}, "same_name_different_content"),
        (
            {"movie.mkv": b"aaa", "es.srt": b"s", "en.ass": b"sub"},
            "destination_has_additional_entries",
        ),
        (
            {"movie.mkv": b"aaa"},
            "destination_missing_entries_possible_partial_transfer",
        ),
        (
            {"remastered.mkv": b"aaa", "es.srt": b"s"},
            "different_releases_or_companion_files",
        ),
    ],
)
def test_conflicts_preserve_both_trees_and_continue(library, destination_files, reason):
    config, raw, temp, vose = library
    movie = make_movie(
        raw / "[g-Drama] A (2001)", {"movie.mkv": b"aaa", "es.srt": b"s"}
    )
    destination = make_movie(vose / "DRAMA/A (2001)", destination_files)
    make_movie(raw / "[g-Comedy] B (2011)")
    before = snapshot(movie, destination)
    report = config.with_name("results.json")
    assert main(["--config", str(config), "--apply", "--report", str(report)]) == 2
    assert snapshot(movie, destination) == before
    assert (vose / "COMEDY/B (2011)/movie.mkv").is_file()
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["counts"] == {"conflict": 1, "completed": 3}
    conflict = result["operations"][0]
    assert (conflict["source"], conflict["destination"], conflict["reason"]) == (
        str(movie),
        str(destination),
        reason,
    )


def test_two_raw_names_that_clean_to_same_destination(library):
    config, raw, temp, vose = library
    first = make_movie(raw / "[g-Drama][d-A] Film", {"movie.mkv": b"A"})
    second = make_movie(raw / "[g-Drama][d-B] Film", {"movie.mkv": b"B"})
    assert main(["--config", str(config), "--apply"]) == 2
    assert (first / "movie.mkv").read_bytes() == b"A"
    assert (second / "movie.mkv").read_bytes() == b"B"
    assert not (vose / "DRAMA/Film").exists()


def test_pending_temp_is_preserved_until_explicit_resume(library):
    config, raw, temp, vose = library
    legacy = make_movie(temp / "DRAMA/[g-Drama][d-Kim] Recovered (2012)")
    (temp / "loose.iso").write_bytes(b"untouched")
    before = snapshot(raw, temp, vose)
    assert main(["--config", str(config), "--dry-run", "--resume"]) == 2
    assert main(["--config", str(config), "--apply"]) == 2
    assert snapshot(raw, temp, vose) == before
    assert main(["--config", str(config), "--apply", "--resume"]) == 2
    assert not legacy.exists()
    assert (vose / "DRAMA/Recovered (2012)/movie.mkv").is_file()
    assert (temp / "loose.iso").read_bytes() == b"untouched"


def test_failed_final_move_can_resume_from_disk(library, monkeypatch):
    config, raw, temp, vose = library
    movie = make_movie(raw / "[g-Drama] Recover Me")
    real = local_filesystem.rename_noreplace

    def denied(source, destination):
        if vose in destination.parents:
            raise PermissionError(errno.EACCES, "synthetic permission failure")
        real(source, destination)

    args = ["--config", str(config), "--apply"]
    with monkeypatch.context() as patch:
        patch.setattr(local_filesystem, "rename_noreplace", denied)
        assert main(args) == 1
    assert not movie.exists()
    assert (temp / "DRAMA/Recover Me/movie.mkv").is_file()
    assert main([*args, "--resume"]) == 0
    assert (vose / "DRAMA/Recover Me/movie.mkv").is_file()


def test_apply_can_stop_before_known_conflict(library):
    config, raw, temp, vose = library
    make_movie(raw / "[g-Drama] A")
    make_movie(vose / "DRAMA/A")
    make_movie(raw / "[g-Comedy] B")
    before = snapshot(raw, temp, vose)
    assert main(["--config", str(config), "--apply", "--stop-on-conflict"]) == 2
    assert snapshot(raw, temp, vose) == before


def test_apply_respects_config_dry_run(library):
    config, raw, temp, vose = library
    data = json.loads(config.read_text(encoding="utf-8"))
    data["dry_run"] = True
    config.write_text(json.dumps(data), encoding="utf-8")
    make_movie(raw / "[g-Drama] A")
    before = snapshot(raw, temp, vose)
    assert main(["--config", str(config), "--apply"]) == 1
    assert snapshot(raw, temp, vose) == before


def test_report_inside_library_is_refused_before_apply(library):
    config, raw, temp, vose = library
    make_movie(raw / "[g-Drama] A")
    before = snapshot(raw, temp, vose)
    assert (
        main(["--config", str(config), "--apply", "--report", str(raw / "plan.json")])
        == 1
    )
    assert snapshot(raw, temp, vose) == before


def test_occupied_apply_lock_is_preserved(library):
    config, raw, temp, vose = library
    make_movie(raw / "[g-Drama] A")
    lock = raw / ".pymovie-manager.lock"
    lock.write_text("other run", encoding="utf-8")
    before = snapshot(raw, temp, vose)
    assert main(["--config", str(config), "--apply"]) == 1
    assert snapshot(raw, temp, vose) == before


def test_resume_keeps_legacy_partial_transfer_markers(library):
    config, raw, temp, vose = library
    make_movie(
        temp / "DRAMA/Old Movie",
        {"AlreadyCopied_feature.mkv": b"data", "extras.txt": b"notes"},
    )
    before = snapshot(raw, temp, vose)
    assert main(["--config", str(config), "--apply", "--resume"]) == 2
    assert snapshot(raw, temp, vose) == before
