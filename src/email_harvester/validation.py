"""Validation and runtime guardrails."""

from __future__ import annotations

import random
import socket
import time
from pathlib import Path
from urllib.parse import urlparse

import dns.resolver

from .errors import ConfigError


def polite_sleep(min_delay: float, max_delay: float) -> None:
    """Sleep within configured bounds."""
    time.sleep(random.uniform(min_delay, max_delay))


def is_supported_url(url: str) -> bool:
    """Allow only absolute HTTP(S) URLs with a hostname."""
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_urls(urls: list[str]) -> list[str]:
    """Normalize and dedupe candidate URL list."""
    output: list[str] = []
    seen: set[str] = set()
    for raw in urls:
        value = raw.strip()
        if not is_supported_url(value):
            continue
        key = value.split("?", maxsplit=1)[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def load_lines_from_file(path: str) -> list[str]:
    """Load non-empty lines from a UTF-8 text file."""
    content = Path(path).read_text(encoding="utf-8")
    return [line.strip() for line in content.splitlines() if line.strip()]


def validate_runtime_constraints(
    *,
    categories: tuple[str, ...],
    seeds: tuple[str, ...],
    workers: int,
    min_delay: float,
    max_delay: float,
    max_results_per_query: int,
    max_hunter_verifications: int,
) -> None:
    """Validate CLI/runtime configuration and raise ConfigError on invalid values."""
    if not categories and not seeds:
        raise ConfigError("Provide --categories/--categories-file or --seeds-file.")
    if workers < 1:
        raise ConfigError("--workers must be >= 1.")
    if min_delay < 0 or max_delay < 0:
        raise ConfigError("--min-delay and --max-delay must be >= 0.")
    if min_delay > max_delay:
        raise ConfigError("--min-delay cannot be greater than --max-delay.")
    if max_results_per_query < 1:
        raise ConfigError("--max-results-per-query must be >= 1.")
    if max_hunter_verifications < 0:
        raise ConfigError("--max-hunter-verifications must be >= 0.")


def mx_check(email: str) -> bool:
    """Return True when target domain has MX or A record."""
    try:
        domain = email.split("@", maxsplit=1)[1]
    except IndexError:
        return False
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=8)
        return bool(answers)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        try:
            socket.gethostbyname(domain)
            return True
        except OSError:
            return False
    except dns.exception.DNSException:
        return False
