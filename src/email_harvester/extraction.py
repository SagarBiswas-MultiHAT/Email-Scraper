"""Pure extraction and URL normalization utilities."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

CONTACT_HINTS = [
    "/contact",
    "/contact-us",
    "/about",
    "/team",
    "/author",
    "/bio",
    "/profile",
    "/get-in-touch",
]
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)


def canonicalize_url(href: str, base: str) -> str:
    """Resolve relative URLs and strip hash fragments."""
    return urljoin(base, href).split("#", maxsplit=1)[0]


def domain_from_url(url: str) -> str:
    """Extract lowercase hostname from URL."""
    return urlparse(url).netloc.lower()


def extract_emails(text: str) -> set[str]:
    """Return normalized emails discovered in plain text."""
    return {match.group(0).lower() for match in EMAIL_REGEX.finditer(text or "")}


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """Dedupe values while preserving first-seen order."""
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.split("#", maxsplit=1)[0]
        if normalized in seen:
            continue
        seen.add(normalized)
        output.append(item)
    return output


def find_contact_links(html: str, base_url: str) -> list[str]:
    """Find contact and about links plus mailto addresses from a page."""
    links: list[str] = []
    soup = BeautifulSoup(html or "", "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        if href.lower().startswith("mailto:"):
            address = href.split(":", maxsplit=1)[1].split("?", maxsplit=1)[0].strip()
            if address:
                links.append(f"mailto:{address}")
            continue
        lower_href = href.lower()
        if any(hint in lower_href for hint in CONTACT_HINTS):
            links.append(canonicalize_url(href, base_url))
    return dedupe_preserve_order(links)
