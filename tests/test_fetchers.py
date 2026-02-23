import logging
from typing import Any

import pytest
import requests

from email_harvester.errors import FetchError
from email_harvester.fetchers import (
    RequestsFetcher,
    RobotsPolicy,
    SeleniumFetcher,
    make_retry_session,
)


class FakeRobotsPolicy:
    def __init__(self, allowed: bool) -> None:
        self._allowed = allowed

    def allowed(self, _url: str) -> bool:
        return self._allowed


class FakeResponse:
    def __init__(self, *, status_code: int = 200, text: str = "") -> None:
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.RequestException("bad status")


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self._response = response
        self.calls: list[str] = []

    def get(self, url: str, **_kwargs: Any) -> FakeResponse:
        self.calls.append(url)
        return self._response


def test_requests_fetcher_rejects_invalid_urls() -> None:
    session = FakeSession(FakeResponse(text="<html/>"))
    fetcher = RequestsFetcher(
        session=session,  # type: ignore[arg-type]
        robots_policy=FakeRobotsPolicy(allowed=True),  # type: ignore[arg-type]
        timeout=5.0,
        logger=logging.getLogger("test"),
    )
    assert fetcher.fetch("file:///tmp/test") == ""
    assert session.calls == []


def test_requests_fetcher_skips_blocked_robots() -> None:
    session = FakeSession(FakeResponse(text="<html/>"))
    fetcher = RequestsFetcher(
        session=session,  # type: ignore[arg-type]
        robots_policy=FakeRobotsPolicy(allowed=False),  # type: ignore[arg-type]
        timeout=5.0,
        logger=logging.getLogger("test"),
    )
    assert fetcher.fetch("https://example.com") == ""
    assert session.calls == []


def test_requests_fetcher_returns_html_for_success() -> None:
    session = FakeSession(FakeResponse(text="<p>Hello</p>"))
    fetcher = RequestsFetcher(
        session=session,  # type: ignore[arg-type]
        robots_policy=FakeRobotsPolicy(allowed=True),  # type: ignore[arg-type]
        timeout=5.0,
        logger=logging.getLogger("test"),
    )
    assert fetcher.fetch("https://example.com") == "<p>Hello</p>"
    assert session.calls == ["https://example.com"]


def test_make_retry_session_sets_user_agent() -> None:
    session = make_retry_session("my-agent")
    assert session.headers["User-Agent"] == "my-agent"


class FakeRobotParser:
    def __init__(self, should_allow: bool, read_error: bool = False) -> None:
        self.url: str | None = None
        self._should_allow = should_allow
        self._read_error = read_error

    def set_url(self, value: str) -> None:
        self.url = value

    def read(self) -> None:
        if self._read_error:
            raise OSError("cannot read robots")

    def can_fetch(self, user_agent: str, _url: str) -> bool:
        _ = user_agent
        return self._should_allow


def test_robots_policy_blocks_when_parser_disallows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "email_harvester.fetchers.urllib.robotparser.RobotFileParser",
        lambda: FakeRobotParser(should_allow=False),
    )
    policy = RobotsPolicy("agent")
    assert policy.allowed("https://example.com/path") is False


def test_robots_policy_allows_when_robots_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "email_harvester.fetchers.urllib.robotparser.RobotFileParser",
        lambda: FakeRobotParser(should_allow=True, read_error=True),
    )
    policy = RobotsPolicy("agent")
    assert policy.allowed("https://example.com/path") is True


def test_selenium_fetcher_import_error_path() -> None:
    with pytest.raises(FetchError):
        SeleniumFetcher(user_agent="agent", logger=logging.getLogger("test"))


def test_selenium_fetcher_fetch_and_close_on_stub_driver() -> None:
    class Driver:
        def __init__(self) -> None:
            self.closed = False
            self.page_source = "<html/>"

        def get(self, _url: str) -> None:
            return None

        def quit(self) -> None:
            self.closed = True

    fetcher = SeleniumFetcher.__new__(SeleniumFetcher)
    fetcher._driver = Driver()  # type: ignore[attr-defined]
    fetcher._logger = logging.getLogger("test")  # type: ignore[attr-defined]

    assert fetcher.fetch("https://example.com") == "<html/>"
    assert fetcher.fetch("file:///tmp/nope") == ""
    fetcher.close()
    assert fetcher._driver.closed is True  # type: ignore[attr-defined]
