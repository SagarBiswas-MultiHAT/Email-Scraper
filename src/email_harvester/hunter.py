"""Hunter API client."""

from __future__ import annotations

import logging
import time
from typing import Any

from requests import Session
from requests.exceptions import RequestException


class HunterClient:
    """Lightweight Hunter API wrapper for domain search and email verification."""

    def __init__(
        self, *, session: Session, api_key: str, timeout: float, logger: logging.Logger
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._timeout = timeout
        self._logger = logger

    def domain_search(self, domain: str, limit: int = 10) -> list[dict[str, Any]]:
        if not domain:
            return []
        params: dict[str, str | int] = {
            "domain": domain,
            "api_key": self._api_key,
            "limit": limit,
        }
        try:
            response = self._session.get(
                "https://api.hunter.io/v2/domain-search",
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except RequestException as exc:
            self._logger.debug("Hunter domain-search failed for %s: %s", domain, exc)
            return []
        emails = payload.get("data", {}).get("emails", [])
        if isinstance(emails, list):
            return [item for item in emails if isinstance(item, dict)]
        return []

    def verify_email(self, email: str, poll: bool = True, timeout: int = 20) -> dict[str, Any]:
        url = "https://api.hunter.io/v2/email-verifier"
        params = {"email": email, "api_key": self._api_key}
        started_at = time.time()
        while True:
            try:
                response = self._session.get(url, params=params, timeout=self._timeout)
            except RequestException as exc:
                return {"status": "error", "exception": str(exc)}
            if response.status_code == 200:
                payload = response.json()
                return payload.get("data", {}) if isinstance(payload, dict) else {}
            if response.status_code == 202 and poll:
                if time.time() - started_at > timeout:
                    return {"status": "timeout"}
                time.sleep(1.0)
                continue
            return {"status": "error", "http_status": response.status_code, "body": response.text}
