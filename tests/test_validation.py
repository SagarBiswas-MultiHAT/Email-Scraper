from pathlib import Path

import dns.resolver
import pytest

from email_harvester.errors import ConfigError
from email_harvester.validation import (
    is_supported_url,
    load_lines_from_file,
    mx_check,
    normalize_urls,
    validate_runtime_constraints,
)


def test_is_supported_url_and_normalize() -> None:
    urls = ["https://example.com/a", "ftp://example.com/file", "https://example.com/a?x=1"]
    assert is_supported_url(urls[0]) is True
    assert is_supported_url(urls[1]) is False
    assert normalize_urls(urls) == ["https://example.com/a"]


def test_validate_runtime_constraints_rejects_invalid_workers() -> None:
    with pytest.raises(ConfigError):
        validate_runtime_constraints(
            categories=("seo",),
            seeds=tuple(),
            workers=0,
            min_delay=0.5,
            max_delay=1.0,
            max_results_per_query=1,
            max_hunter_verifications=0,
        )


def test_validate_runtime_constraints_rejects_empty_inputs() -> None:
    with pytest.raises(ConfigError):
        validate_runtime_constraints(
            categories=tuple(),
            seeds=tuple(),
            workers=1,
            min_delay=0.5,
            max_delay=1.0,
            max_results_per_query=1,
            max_hunter_verifications=0,
        )


def test_validate_runtime_constraints_rejects_delay_and_limits() -> None:
    with pytest.raises(ConfigError):
        validate_runtime_constraints(
            categories=("x",),
            seeds=tuple(),
            workers=1,
            min_delay=2.0,
            max_delay=1.0,
            max_results_per_query=1,
            max_hunter_verifications=0,
        )
    with pytest.raises(ConfigError):
        validate_runtime_constraints(
            categories=("x",),
            seeds=tuple(),
            workers=1,
            min_delay=0,
            max_delay=1,
            max_results_per_query=0,
            max_hunter_verifications=0,
        )
    with pytest.raises(ConfigError):
        validate_runtime_constraints(
            categories=("x",),
            seeds=tuple(),
            workers=1,
            min_delay=0,
            max_delay=1,
            max_results_per_query=1,
            max_hunter_verifications=-1,
        )


def test_load_lines_from_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("one\n\n two \n", encoding="utf-8")
    assert load_lines_from_file(str(sample)) == ["one", "two"]


def test_mx_check_fallback_to_a_record(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_resolve(*_args: object, **_kwargs: object) -> object:
        raise dns.resolver.NoAnswer()

    def fake_gethostbyname(_domain: str) -> str:
        return "127.0.0.1"

    monkeypatch.setattr("email_harvester.validation.dns.resolver.resolve", fake_resolve)
    monkeypatch.setattr("email_harvester.validation.socket.gethostbyname", fake_gethostbyname)

    assert mx_check("user@example.com") is True


def test_mx_check_invalid_email_and_dns_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    assert mx_check("invalid-email") is False

    def fake_resolve(*_args: object, **_kwargs: object) -> object:
        raise dns.exception.Timeout()

    monkeypatch.setattr("email_harvester.validation.dns.resolver.resolve", fake_resolve)
    assert mx_check("user@example.com") is False
