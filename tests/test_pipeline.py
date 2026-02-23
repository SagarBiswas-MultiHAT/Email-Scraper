import logging

from email_harvester.config import HarvestConfig
from email_harvester.models import Fetcher, SearchBackend
from email_harvester.pipeline import harvest_records, run_pipeline


class DummySearchBackend(SearchBackend):
    def search(self, query: str, num: int, min_delay: float, max_delay: float) -> list[str]:
        _ = (query, num, min_delay, max_delay)
        return ["https://example.com"]


class DummyFetcher(Fetcher):
    def __init__(self) -> None:
        self.pages = {
            "https://example.com": '<a href="/contact">Contact</a><a href="mailto:sales@example.com">Mail</a> info@example.com',
            "https://example.com/contact": "support@example.com",
        }

    def fetch(self, url: str) -> str:
        return self.pages.get(url, "")


class DummyHunterClient:
    def __init__(self) -> None:
        self.verify_calls: list[str] = []

    def domain_search(self, domain: str, limit: int = 10) -> list[dict[str, object]]:
        _ = limit
        if domain == "example.com":
            return [{"value": "team@example.com", "confidence": 87}]
        return []

    def verify_email(self, email: str, poll: bool = True, timeout: int = 20) -> dict[str, object]:
        _ = (poll, timeout)
        self.verify_calls.append(email)
        return {"result": "deliverable", "confidence": 95}


def _no_sleep(_min_delay: float, _max_delay: float) -> None:
    return None


def test_harvest_records_with_hunter_and_contact_discovery() -> None:
    config = HarvestConfig(
        categories=("seo",),
        seeds=tuple(),
        output="out.csv",
        hunter_key="hunter-key",
        use_hunter=True,
        use_hunter_domain_search=True,
        yes_run_hunter=True,
        max_hunter_verifications=2,
        min_delay=0,
        max_delay=0,
        show_progress=False,
    )
    hunter = DummyHunterClient()
    rows = harvest_records(
        config=config,
        search_backend=DummySearchBackend(),
        requests_fetcher=DummyFetcher(),
        hunter_client=hunter,
        mx_checker=lambda _email: True,
        sleep_fn=_no_sleep,
        logger=logging.getLogger("test"),
    )

    emails = {row["email"] for row in rows}
    assert {
        "info@example.com",
        "sales@example.com",
        "support@example.com",
        "team@example.com",
    } <= emails
    assert len(hunter.verify_calls) == 2
    assert all(row["mx_ok"] == "yes" for row in rows)


def test_preview_mode_skips_hunter_verification_calls() -> None:
    config = HarvestConfig(
        categories=("seo",),
        seeds=tuple(),
        output="out.csv",
        hunter_key="hunter-key",
        use_hunter=True,
        use_hunter_domain_search=False,
        preview_hunter_costs=True,
        yes_run_hunter=False,
        min_delay=0,
        max_delay=0,
        show_progress=False,
    )
    hunter = DummyHunterClient()
    rows = harvest_records(
        config=config,
        search_backend=DummySearchBackend(),
        requests_fetcher=DummyFetcher(),
        hunter_client=hunter,
        mx_checker=lambda _email: False,
        sleep_fn=_no_sleep,
        logger=logging.getLogger("test"),
    )

    assert rows
    assert hunter.verify_calls == []


def test_run_pipeline_writes_rows(monkeypatch) -> None:
    config = HarvestConfig(
        categories=("seo",),
        seeds=tuple(),
        output="out.csv",
        min_delay=0,
        max_delay=0,
        show_progress=False,
    )
    captured: dict[str, object] = {}

    def fake_harvest_records(**_kwargs):
        return [
            {
                "email": "a@example.com",
                "first_seen_source": "https://example.com",
                "all_sources": "https://example.com",
                "domain": "example.com",
                "mx_ok": "yes",
                "hunter_result": "",
                "hunter_confidence": "",
                "quality": "High",
                "date_scraped_utc": "2026-01-01T00:00:00Z",
                "notes": "page",
            }
        ]

    def fake_write_rows(path: str, rows: list[dict[str, str]]) -> None:
        captured["path"] = path
        captured["rows"] = rows

    monkeypatch.setattr("email_harvester.pipeline.harvest_records", fake_harvest_records)
    monkeypatch.setattr("email_harvester.pipeline.write_rows", fake_write_rows)

    output = run_pipeline(config, logger=logging.getLogger("test"))
    assert output == "out.csv"
    assert captured["path"] == "out.csv"


def test_harvest_records_selenium_mode_closes_fetcher() -> None:
    config = HarvestConfig(
        categories=("seo",),
        seeds=tuple(),
        output="out.csv",
        use_selenium=True,
        min_delay=0,
        max_delay=0,
        show_progress=False,
    )

    class DummySeleniumFetcher:
        def __init__(self) -> None:
            self.closed = False

        def fetch(self, _url: str) -> str:
            return "one@example.com"

        def close(self) -> None:
            self.closed = True

    fetcher = DummySeleniumFetcher()
    rows = harvest_records(
        config=config,
        search_backend=DummySearchBackend(),
        requests_fetcher=DummyFetcher(),
        selenium_fetcher_factory=lambda: fetcher,
        hunter_client=None,
        mx_checker=lambda _email: True,
        sleep_fn=_no_sleep,
        logger=logging.getLogger("test"),
    )
    assert rows
    assert fetcher.closed is True
