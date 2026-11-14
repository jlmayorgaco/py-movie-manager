import csv
import json
import socket

from conftest import make_movie, snapshot
from main import main


def test_inventory_is_local_unicode_preserves_duplicates_and_ignores_extras(
    library, monkeypatch
):
    config, raw, temp, vose = library
    name = "León 日本 (1994)"
    make_movie(
        vose / "DRAMA" / name,
        {
            f"{name} {{edition-Director's Cut}}.mkv": b"first",
            f"{name} 1080p.mp4": b"second",
            f"{name}-trailer.mp4": b"trailer",
            "behind-the-scenes/anything.mkv": b"extra",
            "sample.mp4": b"sample",
            "es.srt": b"subtitle",
            "@eaDir/garbage.mkv": b"thumb",
            ".actors/@eaDir/garbage.mkv": b"nested thumb",
        },
    )
    make_movie(
        raw / "[g-Drama][d-Bong Joon-ho] 기생충 (2019)", {"video.mkv": b"feature"}
    )
    (vose / "Título sin año.MOV").write_bytes(b"feature")
    (vose / "Blade Runner 2049.mkv").write_bytes(b"feature")
    (vose / "=danger.iso").write_bytes(b"feature")
    for excluded in ("#recycle", "@Recycle", ".deletedByTMM", ".pymovie-transfer-test"):
        make_movie(vose / excluded)
    make_movie(temp / "DRAMA/Unpublished")
    dubbed = make_movie(config.parent / "Dubbed", {"La vie (2009).iso": b"dubbed"})
    data = json.loads(config.read_text(encoding="utf-8"))
    data["inventory_roots"] = {"Dubbed": str(dubbed)}
    config.write_text(json.dumps(data), encoding="utf-8")

    def unexpected(*args, **kwargs):
        raise AssertionError("inventory tried to use the network")

    monkeypatch.setattr(socket, "socket", unexpected)
    before = snapshot(raw, temp, vose, dubbed)
    csv_path = config.with_name("catalog.csv")
    assert (
        main(
            [
                "--os",
                "synology",
                "--config",
                str(config),
                "--inventory",
                "--output",
                str(csv_path),
            ]
        )
        == 0
    )
    assert snapshot(raw, temp, vose, dubbed) == before
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 7
    copies = [row for row in rows if row["title"] == "León 日本"]
    assert len(copies) == 2 and {row["extension"] for row in copies} == {".mkv", ".mp4"}
    assert {row["edition_release"] for row in copies} == {"Director's Cut", "1080p"}
    assert all(row["year"] == "1994" and row["genre"] == "Drama" for row in copies)
    korean = next(row for row in rows if row["title"] == "기생충")
    assert (korean["director"], korean["year"], korean["source_library"]) == (
        "Bong Joon-ho",
        "2019",
        "RAW",
    )
    unknown = next(row for row in rows if row["title"] == "Título sin año")
    assert not unknown["year"] and not unknown["genre"] and not unknown["director"]
    assert unknown["needs_review"] == "True"
    assert (
        next(row for row in rows if row["title"] == "Blade Runner 2049")["year"] == ""
    )
    assert any(row["original_name"] == "'=danger.iso" for row in rows)
    assert any(row["source_library"] == "Dubbed" for row in rows)
    assert "watched" not in rows[0]


def test_inventory_accepts_only_configured_roots_and_can_export_text(library):
    config, raw, temp, vose = library
    (vose / "劇場 (2012).m4v").write_bytes(b"feature")
    config.write_text(json.dumps({"directory_vose": str(vose)}), encoding="utf-8")
    path = config.with_name("titles.txt")
    assert main(["--config", str(config), "--inventory", "--output", str(path)]) == 0
    assert "劇場 (2012)" in path.read_text(encoding="utf-8")
    assert main(["--config", str(config), "--inventory", "--output", str(path)]) == 1
    assert (
        main(
            [
                "--config",
                str(config),
                "--inventory",
                "--output",
                str(vose / "titles.txt"),
            ]
        )
        == 1
    )
    assert not (vose / "titles.txt").exists()
