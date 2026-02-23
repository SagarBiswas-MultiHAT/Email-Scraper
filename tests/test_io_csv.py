from pathlib import Path

from email_harvester.io_csv import CSV_FIELDS, write_rows


def test_write_rows_creates_csv_with_schema(tmp_path: Path) -> None:
    output = tmp_path / "out.csv"
    write_rows(
        str(output),
        [
            {
                "email": "a@example.com",
                "first_seen_source": "https://example.com",
                "all_sources": "https://example.com",
                "domain": "example.com",
                "mx_ok": "yes",
                "hunter_result": "deliverable",
                "hunter_confidence": "90",
                "quality": "High",
                "date_scraped_utc": "2026-01-01T00:00:00Z",
                "notes": "page",
            }
        ],
    )
    text = output.read_text(encoding="utf-8")
    assert text.splitlines()[0] == ",".join(CSV_FIELDS)
    assert "a@example.com" in text
