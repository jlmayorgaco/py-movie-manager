import json
from pathlib import Path

import pytest

import main as cli
from conftest import make_movie, snapshot, symlink


def update(path, **values):
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(values)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize(
    "problem", ["same", "nested", "relative", "missing", "non_directory"]
)
def test_invalid_roots_fail_before_any_movie_operation(library, problem):
    config, raw, temp, vose = library
    make_movie(raw / "[g-Drama] A")
    (raw / "child").mkdir()
    (raw / "notdir").write_bytes(b"test")
    values = {
        "same": raw,
        "nested": raw / "child",
        "relative": Path("relative"),
        "missing": config.parent / "missing",
        "non_directory": raw / "notdir",
    }
    update(config, directory_vose=str(values[problem]))
    before = snapshot(raw, temp, vose)
    assert cli.main(["--config", str(config), "--apply"]) == 1
    assert snapshot(raw, temp, vose) == before


def test_library_and_output_symlinks_are_rejected(library):
    config, raw, temp, vose = library
    alias = config.with_name("alias")
    symlink(alias, vose)
    update(config, directory_vose=str(alias))
    assert cli.main(["--config", str(config), "--apply"]) == 1
    update(config, directory_vose=str(vose))
    assert (
        cli.main(
            [
                "--config",
                str(config),
                "--inventory",
                "--output",
                str(alias / "films.csv"),
            ]
        )
        == 1
    )
    assert not (vose / "films.csv").exists()


def test_symlinks_in_movie_folders_are_not_followed(library):
    config, raw, temp, vose = library
    outside = make_movie(config.parent / "outside", {"hidden.mkv": b"do not read"})
    movie = make_movie(raw / "[g-Drama] A")
    symlink(movie / "linked", outside)
    before = snapshot(raw, temp, vose, outside)
    assert cli.main(["--config", str(config), "--apply"]) == 2
    assert snapshot(raw, temp, vose, outside) == before
    inventory = config.with_name("movies.txt")
    assert (
        cli.main(["--config", str(config), "--inventory", "--output", str(inventory)])
        == 0
    )
    assert "hidden.mkv" not in inventory.read_text(encoding="utf-8")


def test_sandbox_uses_only_fixture_and_still_requires_apply(library, monkeypatch):
    config, raw, temp, vose = library
    checkout = config.parent / "checkout"
    sandbox = checkout / "__sandbox__"
    sandbox_raw = sandbox / "__RAW__"
    sandbox_temp = sandbox / "__TMM_TEMP__"
    sandbox_vose = sandbox / "__VOSE__"
    make_movie(sandbox_raw / "[g-Drama] Sandbox")
    sandbox_vose.mkdir()
    make_movie(raw / "[g-Drama] Real")
    (checkout / "config").mkdir()
    sandbox_config = checkout / "config/config.sandbox.json"
    sandbox_config.write_text(
        (cli.BASE_DIR / "config/config.sandbox.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "BASE_DIR", checkout)
    before = snapshot(raw, temp, vose, sandbox_raw, sandbox_temp, sandbox_vose)
    assert cli.main(["--sandbox"]) == 0
    assert snapshot(raw, temp, vose, sandbox_raw, sandbox_temp, sandbox_vose) == before
    update(sandbox_config, directory_raw=str(raw))
    assert cli.main(["--sandbox", "--apply"]) == 1
    assert snapshot(raw, temp, vose, sandbox_raw, sandbox_temp, sandbox_vose) == before
