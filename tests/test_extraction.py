from email_harvester.extraction import (
    canonicalize_url,
    domain_from_url,
    extract_emails,
    find_contact_links,
)


def test_extract_emails_normalizes_and_dedupes() -> None:
    text = "Contact A@Example.com, again a@example.com, and b@example.org."
    assert extract_emails(text) == {"a@example.com", "b@example.org"}


def test_find_contact_links_collects_mailto_and_contact_pages() -> None:
    html = """
    <html>
      <body>
        <a href="/contact">Contact</a>
        <a href="/contact">Contact Again</a>
        <a href="mailto:Team@example.com?subject=Hello">Email us</a>
      </body>
    </html>
    """
    links = find_contact_links(html, "https://example.com/path")
    assert links == ["https://example.com/contact", "mailto:Team@example.com"]


def test_url_helpers() -> None:
    assert (
        canonicalize_url("/about#team", "https://example.com/home") == "https://example.com/about"
    )
    assert domain_from_url("https://Sub.Example.com/path") == "sub.example.com"
