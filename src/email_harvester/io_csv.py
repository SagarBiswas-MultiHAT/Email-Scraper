"""CSV serialization helpers."""

from __future__ import annotations

import csv
from pathlib import Path

CSV_FIELDS = [
    "email",
    "first_seen_source",
    "all_sources",
    "domain",
    "mx_ok",
    "hunter_result",
    "hunter_confidence",
    "quality",
    "date_scraped_utc",
    "notes",
]


def write_rows(path: str, rows: list[dict[str, str]]) -> None:
    """Write harvest rows to CSV with stable schema."""
    output_path = Path(path)
    with output_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
