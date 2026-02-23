import logging
from typing import Any

import requests

from email_harvester.search_backends import FallbackSearchBackend


class FakeResponse:
    def __init__(
        self, *, status_code: int = 200, text: str = "", payload: dict[str, Any] | None = None
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.RequestException(f"http error {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    def __init__(self, mapping: dict[str, FakeResponse]) -> None:
        self.mapping = mapping
        self.calls: list[str] = []

    def get(self, url: str, **_kwargs: Any) -> FakeResponse:
        self.calls.append(url)
        return self.mapping[url]


def test_prefers_serpapi_when_available() -> None:
    session = FakeSession(
        {
            "https://serpapi.com/search.json": FakeResponse(
                payload={"organic_results": [{"link": "https://example.com"}]}
            )
        }
    )
    backend = FallbackSearchBackend(
        session=session,  # type: ignore[arg-type]
        user_agent="agent",
        timeout=10.0,
        serpapi_key="key",
        bing_key="bing",
        logger=logging.getLogger("test"),
    )
    urls = backend.search("q", 5, 0, 0)
    assert urls == ["https://example.com"]
    assert session.calls == ["https://serpapi.com/search.json"]


def test_falls_back_to_bing_when_serpapi_fails() -> None:
    session = FakeSession(
        {
            "https://serpapi.com/search.json": FakeResponse(status_code=500),
            "https://api.bing.microsoft.com/v7.0/search": FakeResponse(
                payload={"webPages": {"value": [{"url": "https://bing-result.com"}]}}
            ),
        }
    )
    backend = FallbackSearchBackend(
        session=session,  # type: ignore[arg-type]
        user_agent="agent",
        timeout=10.0,
        serpapi_key="key",
        bing_key="bing",
        logger=logging.getLogger("test"),
    )
    urls = backend.search("q", 5, 0, 0)
    assert urls == ["https://bing-result.com"]
    assert session.calls == [
        "https://serpapi.com/search.json",
        "https://api.bing.microsoft.com/v7.0/search",
    ]


def test_falls_back_to_duckduckgo_without_keys() -> None:
    html = """
    <html><body>
      <a href="/l/?uddg=https%3A%2F%2Fexample.org%2Fabout">Result</a>
      <a href="https://duckduckgo.com/internal">Internal</a>
    </body></html>
    """
    session = FakeSession({"https://html.duckduckgo.com/html/": FakeResponse(text=html)})
    backend = FallbackSearchBackend(
        session=session,  # type: ignore[arg-type]
        user_agent="agent",
        timeout=10.0,
        serpapi_key=None,
        bing_key=None,
        logger=logging.getLogger("test"),
    )
    urls = backend.search("q", 5, 0, 0)
    assert urls == ["https://example.org/about"]
    assert session.calls == ["https://html.duckduckgo.com/html/"]
