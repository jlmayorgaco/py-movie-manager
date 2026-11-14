"""CSV, TXT and JSON output, only through an exclusively opened destination."""

import csv
import json
from dataclasses import asdict, fields
from typing import TextIO

from src.domain.classes.Inventory import Record
from src.domain.classes.MovieManagerClass import Run


def _excel_cell(value):
    # Excel interprets some untrusted filenames as formulas, even in quoted CSV.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_csv(stream: TextIO, records: list[Record]) -> None:
    writer = csv.DictWriter(stream, fieldnames=[item.name for item in fields(Record)])
    writer.writeheader()
    for record in records:
        writer.writerow(
            {key: _excel_cell(value) for key, value in asdict(record).items()}
        )


def write_text(stream: TextIO, records: list[Record]) -> None:
    for record in records:
        year = f" ({record.year})" if record.year else ""
        review = " [review]" if record.needs_review else ""
        stream.write(
            f"{record.title}{year}{review} | {record.source_library} | {record.path}\n"
        )


def write_report(stream: TextIO, run: Run) -> None:
    json.dump(run.as_dict(), stream, ensure_ascii=False, indent=2, default=str)
    stream.write("\n")
