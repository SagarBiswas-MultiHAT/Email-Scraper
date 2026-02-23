"""Search backend implementations and query builder."""

from __future__ import annotations

import logging
from urllib.parse import unquote

from bs4 import BeautifulSoup
from requests import Session
from requests.exceptions import RequestException

from .validation import normalize_urls, polite_sleep


def build_queries(categories: tuple[str, ...]) -> list[str]:
    """Build broad and narrow search queries for each category."""
    queries: list[str] = []
    for category in categories:
        queries.append(
            f'intitle:"contact" "{category}" OR intitle:"about" "{category}" OR "{category}" "contact"'
        )
        queries.append(f'"{category}" site:.com')
        queries.append(f'"{category}" services')
    return queries


def _decode_ddg_href(href: str) -> str | None:
    if not href:
        return None
    if "uddg=" not in href:
        return href
    encoded = href.split("uddg=")[-1]
    return unquote(encoded)


class FallbackSearchBackend:
    """SerpApi -> Bing -> DuckDuckGo fallback search backend."""

    def __init__(
        self,
        session: Session,
        *,
        user_agent: str,
        timeout: float,
        serpapi_key: str | None,
        bing_key: str | None,
        logger: logging.Logger,
    ) -> None:
        self._session = session
        self._user_agent = user_agent
        self._timeout = timeout
        self._serpapi_key = serpapi_key
        self._bing_key = bing_key
        self._logger = logger

    def search(self, query: str, num: int, min_delay: float, max_delay: float) -> list[str]:
        urls: list[str] = []
        if self._serpapi_key:
            urls = self._search_serpapi(query, num)
        if not urls and self._bing_key:
            urls = self._search_bing(query, num)
        if not urls:
            urls = self._search_duckduckgo(query, num, min_delay, max_delay)
        return normalize_urls(urls)[:num]

    def _search_serpapi(self, query: str, num: int) -> list[str]:
        try:
            response = self._session.get(
                "https://serpapi.com/search.json",
                params={"q": query, "engine": "google", "num": num, "api_key": self._serpapi_key},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except RequestException as exc:
            self._logger.warning("SerpApi search failed: %s", exc)
            return []

        output: list[str] = []
        for item in payload.get("organic_results", []):
            link = item.get("link") or item.get("url")
            if isinstance(link, str):
                output.append(link)
        return output

    def _search_bing(self, query: str, num: int) -> list[str]:
        params: dict[str, str | int] = {
            "q": query,
            "count": num,
            "textDecorations": "false",
            "textFormat": "Raw",
        }
        try:
            response = self._session.get(
                "https://api.bing.microsoft.com/v7.0/search",
                params=params,
                headers={
                    "Ocp-Apim-Subscription-Key": self._bing_key,
                    "User-Agent": self._user_agent,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except RequestException as exc:
            self._logger.warning("Bing search failed: %s", exc)
            return []

        output: list[str] = []
        for item in payload.get("webPages", {}).get("value", []):
            link = item.get("url")
            if isinstance(link, str):
                output.append(link)
        return output

    def _search_duckduckgo(
        self, query: str, num: int, min_delay: float, max_delay: float
    ) -> list[str]:
        urls: list[str] = []
        bases = ["https://html.duckduckgo.com/html/", "https://duckduckgo.com/html/"]
        headers = {"User-Agent": self._user_agent}
        for base in bases:
            try:
                response = self._session.get(
                    base,
                    params={"q": query},
                    headers=headers,
                    timeout=self._timeout,
                )
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                for anchor in soup.find_all("a", href=True):
                    href = str(anchor.get("href")).strip()
                    decoded = _decode_ddg_href(href)
                    if decoded and decoded.startswith("http"):
                        href = decoded
                    if href.startswith("javascript:") or "duckduckgo.com" in href:
                        continue
                    if href.startswith("http"):
                        urls.append(href)
                    if len(urls) >= num:
                        break
                if urls:
                    break
            except RequestException as exc:
                self._logger.debug("DuckDuckGo search failed: %s", exc)
            polite_sleep(min_delay, max_delay)
        return urls[:num]
