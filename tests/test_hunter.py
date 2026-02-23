import logging
from typing import Any

import requests

from email_harvester.hunter import HunterClient


class FakeResponse:
    def __init__(
        self, *, status_code: int = 200, payload: dict[str, Any] | None = None, text: str = ""
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.RequestException("request failed")

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    def __init__(
        self, responses: list[FakeResponse] | None = None, raise_error: bool = False
    ) -> None:
        self._responses = responses or []
        self._raise_error = raise_error
        self.calls = 0

    def get(self, _url: str, **_kwargs: Any) -> FakeResponse:
        self.calls += 1
        if self._raise_error:
            raise requests.RequestException("network down")
        if self._responses:
            return self._responses.pop(0)
        return FakeResponse(status_code=500)


def test_domain_search_success() -> None:
    session = FakeSession([FakeResponse(payload={"data": {"emails": [{"value": "a@b.com"}]}})])
    client = HunterClient(
        session=session, api_key="key", timeout=5.0, logger=logging.getLogger("test")
    )  # type: ignore[arg-type]
    assert client.domain_search("example.com") == [{"value": "a@b.com"}]


def test_domain_search_request_failure() -> None:
    session = FakeSession(raise_error=True)
    client = HunterClient(
        session=session, api_key="key", timeout=5.0, logger=logging.getLogger("test")
    )  # type: ignore[arg-type]
    assert client.domain_search("example.com") == []


def test_verify_email_success_and_error_paths() -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=202),
            FakeResponse(payload={"data": {"result": "deliverable"}}),
            FakeResponse(status_code=400, text="bad request"),
        ]
    )
    client = HunterClient(
        session=session, api_key="key", timeout=5.0, logger=logging.getLogger("test")
    )  # type: ignore[arg-type]
    assert client.verify_email("x@example.com", poll=True, timeout=1).get("result") == "deliverable"
    error_payload = client.verify_email("x@example.com", poll=False, timeout=1)
    assert error_payload["status"] == "error"


def test_verify_email_request_exception() -> None:
    session = FakeSession(raise_error=True)
    client = HunterClient(
        session=session, api_key="key", timeout=5.0, logger=logging.getLogger("test")
    )  # type: ignore[arg-type]
    payload = client.verify_email("x@example.com")
    assert payload["status"] == "error"
