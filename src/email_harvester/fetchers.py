"""HTTP and browser fetchers."""

from __future__ import annotations

import logging
import urllib.robotparser
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from .errors import FetchError
from .validation import is_supported_url


class RobotsPolicy:
    """robots.txt cache and allow checks."""

    def __init__(self, user_agent: str) -> None:
        self._user_agent = user_agent
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._lock = Lock()

    def allowed(self, url: str) -> bool:
        """Return True if robots policy allows this URL."""
        if not is_supported_url(url):
            return False
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        with self._lock:
            parser = self._cache.get(origin)
            if parser is None and origin not in self._cache:
                parser = urllib.robotparser.RobotFileParser()
                parser.set_url(origin.rstrip("/") + "/robots.txt")
                try:
                    parser.read()
                    self._cache[origin] = parser
                except OSError:
                    self._cache[origin] = None
                    parser = None
            elif origin in self._cache:
                parser = self._cache[origin]

        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)


def make_retry_session(user_agent: str) -> Session:
    """Create requests session with retry/backoff defaults."""
    session = Session()
    session.headers.update({"User-Agent": user_agent})
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset({"GET", "POST"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class RequestsFetcher:
    """Requests-based fetcher with robots checks."""

    def __init__(
        self,
        *,
        session: Session,
        robots_policy: RobotsPolicy,
        timeout: float,
        logger: logging.Logger,
    ) -> None:
        self._session = session
        self._robots_policy = robots_policy
        self._timeout = timeout
        self._logger = logger

    def fetch(self, url: str) -> str:
        if not is_supported_url(url):
            self._logger.debug("Skipping unsupported URL: %s", url)
            return ""
        if not self._robots_policy.allowed(url):
            self._logger.info("Skipping due to robots.txt: %s", url)
            return ""
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            return str(response.text)
        except RequestException as exc:
            self._logger.debug("Requests fetch failed for %s: %s", url, exc)
            return ""


class SeleniumFetcher:
    """Selenium fetcher with one isolated browser instance."""

    def __init__(self, *, user_agent: str, logger: logging.Logger) -> None:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import (
                Service as ChromeService,
            )
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError as exc:  # pragma: no cover - exercised only when selenium requested
            raise FetchError(
                "Selenium dependencies are not installed. Use pip install .[selenium]."
            ) from exc

        self._logger = logger
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={user_agent}")
        try:
            service = ChromeService(ChromeDriverManager().install())
            self._driver: Any = webdriver.Chrome(service=service, options=options)
        except Exception as exc:  # pragma: no cover - integration behavior
            raise FetchError(f"Failed to start Selenium driver: {exc}") from exc

    def fetch(self, url: str) -> str:
        if not is_supported_url(url):
            return ""
        try:
            self._driver.get(url)
            return str(self._driver.page_source)
        except Exception as exc:  # pragma: no cover - integration behavior
            self._logger.debug("Selenium fetch failed for %s: %s", url, exc)
            return ""

    def close(self) -> None:
        try:
            self._driver.quit()
        except Exception:  # pragma: no cover - integration behavior
            return None
