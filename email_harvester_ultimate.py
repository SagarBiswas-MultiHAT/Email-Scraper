#!/usr/bin/env python3
"""
email_harvester_ultimate.py

Ultimate production-ready email harvester.

Features:
- Multi-backend search: SerpApi (if key) -> Bing Web Search API (if key) -> DuckDuckGo HTML fallback
- Polite crawling with robots.txt checks and configurable rate limits
- Contact/about link discovery and following + mailto extraction
- Optional Selenium support for JS-heavy pages
- Optional Hunter integration (domain-search + email-verifier) with preview and caps
- MX checks using dnspython
- Deduplication, domain-first logic, and CSV export
- Quality scoring (High/Medium/Low) combining Hunter, MX, and source count
- Retries with backoff, optional progress bars
- CLI options for all parameters, seeds mode, and safe defaults

Quick examples:
  # Basic (free, no API keys)
  python email_harvester_ultimate.py --categories-file categories.txt --output results.csv

  # Best (use SerpApi + Hunter; use environment vars or pass keys)
  export SERPAPI_KEY="..."
  export HUNTER_API_KEY="..."
  export BING_API_KEY="..."
  python email_harvester_ultimate.py --categories-file categories.txt --use-hunter --use-hunter-domain-search --yes-run-hunter --max-hunter-verifications 40 --serpapi-key $SERPAPI_KEY --bing-key $BING_API_KEY --output verified_ranked.csv

Dependencies:
  pip install requests beautifulsoup4 dnspython tqdm
  Optional (Selenium): pip install selenium webdriver-manager
"""

from __future__ import annotations
import argparse
import csv
import itertools
import json
import logging
import os
import random
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import dns.resolver

# Optional progress bar
try:
    from tqdm import tqdm  # type: ignore
    TQDM_AVAILABLE = True
except Exception:
    TQDM_AVAILABLE = False

# Optional Selenium
try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.chrome.service import Service as ChromeService  # type: ignore
    from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

# Robust requests session with retries
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------- Configuration ----------
USER_AGENT = "SagarHarvester/2.0 (+mailto:you@example.com)"
REQUEST_TIMEOUT = 15.0
WORKERS_DEFAULT = 8
MIN_DELAY_DEFAULT = 0.9
MAX_DELAY_DEFAULT = 2.2
MAX_RESULTS_PER_QUERY_DEFAULT = 12
CONTACT_HINTS = ["/contact", "/contact-us", "/about", "/team", "/author", "/bio", "/profile", "/get-in-touch"]
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)
CSV_FIELDS = [
    "email",
    "first_seen_source",
    "all_sources",
    "domain",
    "mx_ok",
    "hunter_result",
    "hunter_confidence",
    "quality",
    "date_scraped_utc",
    "notes",
]
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
# ------------------------------------------------

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("harvester")

# session with retries/backoff
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
retries = Retry(total=3, backoff_factor=0.6, status_forcelist=[429,500,502,503,504], allowed_methods=frozenset(['GET','POST']))
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))

_robot_cache: Dict[str, Optional[object]] = {}

# ---------- Utility helpers ----------
def polite_sleep(min_delay: float, max_delay: float) -> None:
    time.sleep(random.uniform(min_delay, max_delay))

def domain_from_url(url: str) -> str:
    try:
        p = urlparse(url)
        return p.netloc.lower()
    except Exception:
        return ""

def canonicalize_url(href: str, base: str) -> str:
    try:
        return urljoin(base, href).split("#")[0]
    except Exception:
        return href

def extract_emails(text: str) -> Set[str]:
    return {m.group(0).lower() for m in EMAIL_REGEX.finditer(text or "")}

# ---------- Robots.txt ----------
import urllib.robotparser
def allowed_by_robots(url: str) -> bool:
    try:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        rp = _robot_cache.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(origin.rstrip("/") + "/robots.txt")
            try:
                rp.read()
            except Exception:
                _robot_cache[origin] = None
                return True
            _robot_cache[origin] = rp
        if _robot_cache[origin] is None:
            return True
        return _robot_cache[origin].can_fetch(USER_AGENT, url)
    except Exception:
        return True

# ---------- Search backends ----------
def _decode_ddg_href(href: str) -> Optional[str]:
    if not href:
        return None
    if "uddg=" in href:
        try:
            parts = href.split("uddg=")
            enc = parts[-1]
            return unquote(enc)
        except Exception:
            return None
    return href

def search_duckduckgo(query: str, num: int, min_delay: float, max_delay: float) -> List[str]:
    """DuckDuckGo HTML fallback. No key required."""
    urls: List[str] = []
    bases = ["https://html.duckduckgo.com/html/", "https://duckduckgo.com/html/"]
    headers = {"User-Agent": USER_AGENT}
    for base in bases:
        try:
            r = session.get(base, params={"q": query}, headers=headers, timeout=REQUEST_TIMEOUT)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            # permissive: any anchor with http href
            for a in soup.find_all("a", href=True):
                href = a.get("href").strip()
                dec = _decode_ddg_href(href)
                if dec and dec.startswith("http"):
                    href = dec
                if href.startswith("javascript:") or "duckduckgo.com" in href:
                    continue
                if href.startswith("http"):
                    urls.append(href)
                if len(urls) >= num:
                    break
            if urls:
                break
        except Exception as e:
            logger.debug("DDG search error: %s", e)
        polite_sleep(min_delay, max_delay)
    # dedupe & normalize
    cleaned: List[str] = []
    seen: Set[str] = set()
    for u in urls:
        try:
            key = u.split("?")[0].rstrip("/")
            if key not in seen:
                seen.add(key)
                cleaned.append(u)
            if len(cleaned) >= num:
                break
        except Exception:
            continue
    return cleaned

def search_serpapi(query: str, api_key: str, num: int) -> List[str]:
    urls: List[str] = []
    if not api_key:
        return urls
    try:
        resp = session.get("https://serpapi.com/search.json", params={"q": query, "engine": "google", "num": num, "api_key": api_key}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        for item in j.get("organic_results", []):
            link = item.get("link") or item.get("url")
            if link:
                urls.append(link)
    except Exception as e:
        logger.warning("SerpApi search error: %s", e)
    return urls

def search_bing(query: str, api_key: str, num: int) -> List[str]:
    """
    Basic Bing Web Search API wrapper (v7/azure). Works if you provide a key.
    Supports 'Ocp-Apim-Subscription-Key' header or 'api-key' depending on endpoint.
    """
    if not api_key:
        return []
    urls = []
    headers = {"Ocp-Apim-Subscription-Key": api_key, "User-Agent": USER_AGENT}
    params = {"q": query, "count": num, "textDecorations": False, "textFormat": "Raw"}
    try:
        resp = session.get("https://api.bing.microsoft.com/v7.0/search", params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        for item in j.get("webPages", {}).get("value", []):
            link = item.get("url")
            if link:
                urls.append(link)
    except Exception as e:
        logger.warning("Bing search error: %s", e)
    return urls

# ---------- Fetchers (requests + selenium) ----------
def fetch_with_requests(url: str) -> str:
    try:
        if not allowed_by_robots(url):
            logger.info("Skipping due to robots.txt: %s", url)
            return ""
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.debug("Requests fetch failed for %s: %s", url, e)
        return ""

def create_selenium_driver(user_agent: str):
    if not SELENIUM_AVAILABLE:
        return None
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={user_agent}")
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logger.error("Failed to start Selenium driver: %s", e)
        return None

def fetch_with_selenium(url: str, driver) -> str:
    try:
        driver.get(url)
        time.sleep(1.0)
        return driver.page_source
    except Exception as e:
        logger.debug("Selenium fetch failed for %s: %s", url, e)
        return ""

def find_contact_links(html: str, base_url: str) -> List[str]:
    links: List[str] = []
    try:
        soup = BeautifulSoup(html or "", "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                addr = href.split(":", 1)[1].split("?")[0]
                if addr:
                    links.append("mailto:" + addr)
                continue
            lower = href.lower()
            for hint in CONTACT_HINTS:
                if hint in lower:
                    links.append(canonicalize_url(href, base_url))
                    break
    except Exception:
        pass
    # dedupe preserve order
    uniq = []
    seen = set()
    for l in links:
        k = l.split("#")[0]
        if k not in seen:
            seen.add(k)
            uniq.append(l)
    return uniq

# ---------- MX check ----------
def mx_check(email: str) -> bool:
    try:
        domain = email.split("@")[-1]
        answers = dns.resolver.resolve(domain, "MX", lifetime=8)
        return bool(answers)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        # fallback to A record
        try:
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False
    except Exception:
        return False

# ---------- Hunter integration ----------
def hunter_domain_search(domain: str, api_key: str, limit: int = 10) -> List[dict]:
    if not api_key:
        return []
    try:
        resp = session.get("https://api.hunter.io/v2/domain-search", params={"domain": domain, "api_key": api_key, "limit": limit}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        return j.get("data", {}).get("emails", []) or []
    except Exception as e:
        logger.debug("Hunter domain-search error: %s", e)
        return []

def hunter_verify_email(email: str, api_key: str, poll: bool = True, timeout: int = 20) -> dict:
    if not api_key:
        return {"status": "no_key"}
    url = "https://api.hunter.io/v2/email-verifier"
    params = {"email": email, "api_key": api_key}
    start = time.time()
    try:
        while True:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json().get("data", {})
            if resp.status_code == 202 and poll:
                if time.time() - start > timeout:
                    return {"status": "timeout"}
                time.sleep(1.0)
                continue
            return {"status": "error", "http_status": resp.status_code, "body": resp.text}
    except Exception as e:
        return {"status": "error", "exception": str(e)}

# ---------- Quality scoring ----------
def _parse_confidence(hv: dict) -> Optional[float]:
    if not isinstance(hv, dict):
        return None
    for k in ("confidence","score"):
        v = hv.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            try:
                return float(str(v))
            except Exception:
                continue
    return None

def _result_is_deliverable(hv: dict) -> bool:
    if not isinstance(hv, dict):
        return False
    for k in ("result","status","status_text","result_code"):
        v = hv.get(k)
        if not v: continue
        s = str(v).strip().lower()
        if s in ("deliverable","deliverable (smtp)","valid","ok","success","deliverable?"):
            return True
    return False

def compute_quality(mx_ok: bool, hunter_res: dict, source_count: int) -> str:
    try:
        if _result_is_deliverable(hunter_res):
            return "High"
    except Exception:
        pass
    conf = _parse_confidence(hunter_res) if hunter_res else None
    if conf is not None:
        # hunter confidence is likely 0-100 or 0-1; normalize if needed
        if conf <= 1.0: conf *= 100.0
        if conf >= 80.0 and (mx_ok or source_count >= 1):
            return "High"
        if 50.0 <= conf < 80.0 and (mx_ok or source_count >= 1):
            return "Medium"
    if mx_ok and source_count >= 3:
        return "High"
    if mx_ok and source_count >= 1:
        return "Medium"
    return "Low"

# ---------- Page processing ----------
def process_page(url: str, use_selenium: bool, driver, min_delay: float, max_delay: float, hunter_key: Optional[str], use_hunter_domain_search: bool) -> List[Tuple[str,str,str]]:
    found: List[Tuple[str,str,str]] = []
    html = ""
    if use_selenium and driver:
        html = fetch_with_selenium(url, driver)
    else:
        html = fetch_with_requests(url)
    if not html:
        return found
    for e in extract_emails(html):
        found.append((e, url, "page"))
    contact_links = find_contact_links(html, url)
    for cl in contact_links:
        if cl.startswith("mailto:"):
            addr = cl.split(":",1)[1].split("?")[0].lower()
            found.append((addr, url, "mailto"))
            continue
        polite_sleep(min_delay, max_delay)
        child_html = fetch_with_selenium(cl, driver) if (use_selenium and driver) else fetch_with_requests(cl)
        if not child_html:
            continue
        for e in extract_emails(child_html):
            found.append((e, cl, "contact_page"))
    if use_hunter_domain_search and hunter_key:
        dom = domain_from_url(url)
        if dom:
            polite_sleep(min_delay, max_delay)
            h_emails = hunter_domain_search(dom, hunter_key, limit=10)
            for he in h_emails:
                val = he.get("value")
                if val:
                    confidence = str(he.get("confidence",""))
                    found.append((val.lower(), url, f"hunter_domain:{confidence}"))
    return found

# ---------- Orchestration ----------
def harvest(
    categories: List[str],
    *,
    serpapi_key: Optional[str] = None,
    bing_key: Optional[str] = None,
    hunter_key: Optional[str] = None,
    use_hunter: bool = False,
    use_hunter_domain_search: bool = False,
    seeds: Optional[List[str]] = None,
    use_selenium: bool = False,
    output: str = "emails_output.csv",
    workers: int = WORKERS_DEFAULT,
    min_delay: float = MIN_DELAY_DEFAULT,
    max_delay: float = MAX_DELAY_DEFAULT,
    max_results_per_query: int = MAX_RESULTS_PER_QUERY_DEFAULT,
    preview_hunter_costs: bool = False,
    max_hunter_verifications: int = 50,
) -> str:
    candidate_urls: List[str] = []
    if seeds:
        candidate_urls = list(dict.fromkeys(seeds))
    else:
        queries: List[str] = []
        for cat in categories:
            # build broad and narrow variants for better discovery
            queries.append(f'intitle:"contact" "{cat}" OR intitle:"about" "{cat}" OR "{cat}" "contact"')
            queries.append(f'"{cat}" site:.com')
            queries.append(f'"{cat}" services')
        # run queries with multi-backend fallback
        for q in queries:
            logger.info("Searching: %s", q)
            urls = []
            # prefer SerpApi
            if serpapi_key:
                urls = search_serpapi(q, serpapi_key, num=max_results_per_query)
            # else try Bing
            if not urls and bing_key:
                urls = search_bing(q, bing_key, num=max_results_per_query)
            # fallback to DuckDuckGo
            if not urls:
                urls = search_duckduckgo(q, num=max_results_per_query, min_delay=min_delay, max_delay=max_delay)
            logger.info(" --> found %d candidate URLs", len(urls))
            candidate_urls.extend(urls)
            polite_sleep(min_delay, max_delay)
        # dedupe preserve order
        uniq: List[str] = []
        seen: Set[str] = set()
        for u in candidate_urls:
            try:
                key = u.split("?")[0].rstrip("/")
                if key not in seen:
                    seen.add(key)
                    uniq.append(u)
            except Exception:
                continue
        candidate_urls = uniq

    logger.info("Total candidate URLs to scan: %d", len(candidate_urls))

    # setup selenium driver if requested
    driver = None
    if use_selenium:
        driver = create_selenium_driver(USER_AGENT)
        if driver is None:
            logger.warning("Selenium requested but driver couldn't be created; continuing without Selenium")
            use_selenium = False

    results: Dict[str, Dict[str, object]] = {}  # email -> {first_source, sources:set, notes}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_page, url, use_selenium, driver, min_delay, max_delay, hunter_key, use_hunter_domain_search): url for url in candidate_urls}
        items_iter = list(futures.items())
        if TQDM_AVAILABLE:
            items_iter = tqdm(items_iter, desc="scanning pages")
        for fut, url in items_iter:
            try:
                items = fut.result()
            except Exception as e:
                logger.debug("Worker failed for %s: %s", url, e)
                items = []
            for email, src, tag in items:
                email = email.lower()
                if email not in results:
                    results[email] = {"first_source": src, "sources": set([src]), "notes": tag}
                else:
                    results[email]["sources"].add(src)

    if driver:
        try:
            driver.quit()
        except Exception:
            pass

    logger.info("Unique emails found on pages: %d", len(results))

    # Hunter verification (preview & caps)
    hunter_summary: Dict[str, dict] = {}
    if use_hunter and hunter_key:
        emails_list = sorted(results.keys())
        estimated = len(emails_list)
        logger.info("Emails that could be verified by Hunter: %d", estimated)
        if preview_hunter_costs:
            logger.info("Preview mode: no Hunter API calls made. Estimated verifications: %d", estimated)
        else:
            to_verify = emails_list[:max_hunter_verifications]
            logger.info("Performing up to %d Hunter verifications (cap).", len(to_verify))
            count = 0
            for e in to_verify:
                polite_sleep(min_delay, max_delay + 0.5)
                hv = hunter_verify_email(e, hunter_key, poll=True, timeout=20)
                hunter_summary[e] = hv
                count += 1
                if count >= max_hunter_verifications:
                    break
            logger.info("Completed Hunter verification calls: %d", len(hunter_summary))

    # prepare CSV rows
    rows = []
    emails_iter = sorted(results.keys())
    if TQDM_AVAILABLE:
        emails_iter = tqdm(emails_iter, desc="verifying & writing")
    for e in emails_iter:
        info = results[e]
        mx_ok = mx_check(e)
        hv = hunter_summary.get(e, {})
        hv_result = hv.get("result") or hv.get("status") or ""
        hv_conf = str(hv.get("confidence") or hv.get("score") or "")
        source_count = len(info["sources"]) if info.get("sources") else 0
        quality = compute_quality(mx_ok, hv, source_count)
        rows.append({
            "email": e,
            "first_seen_source": info["first_source"],
            "all_sources": ";".join(sorted(info["sources"])),
            "domain": domain_from_url(info["first_source"]),
            "mx_ok": "yes" if mx_ok else "no",
            "hunter_result": hv_result,
            "hunter_confidence": hv_conf,
            "quality": quality,
            "date_scraped_utc": datetime.utcnow().isoformat() + "Z",
            "notes": info.get("notes",""),
        })
        polite_sleep(min_delay*0.08, max_delay*0.08)

    # write CSV
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    logger.info("Wrote %d rows to %s", len(rows), output)
    return output

# ---------- CLI & helpers ----------
def load_lines_from_file(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Email Harvester Ultimate - multi-backend, Hunter optional, Selenium optional")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--categories", nargs="+", help="Category keywords")
    g.add_argument("--categories-file", help="File with categories, one per line")
    p.add_argument("--seeds-file", help="File with seed URLs to skip searching")
    p.add_argument("--serpapi-key", help="SerpApi API key (optional)")
    p.add_argument("--bing-key", help="Bing Web Search API key (optional)")
    p.add_argument("--use-selenium", action="store_true", help="Use Selenium (optional)")
    p.add_argument("--use-hunter", action="store_true", help="Enable Hunter verification (optional)")
    p.add_argument("--hunter-key", help="Hunter API key (optional) or set HUNTER_API_KEY env var")
    p.add_argument("--use-hunter-domain-search", action="store_true", help="Use Hunter domain-search per domain (optional)")
    p.add_argument("--preview-hunter-costs", action="store_true", help="Preview Hunter costs, don't call API")
    p.add_argument("--max-hunter-verifications", type=int, default=50, help="Cap on Hunter verifications to perform")
    p.add_argument("--yes-run-hunter", action="store_true", help="Confirm to actually run Hunter verifications (safety)")
    p.add_argument("--output", default="emails_output.csv", help="Output CSV path")
    p.add_argument("--workers", type=int, default=WORKERS_DEFAULT, help="Number of worker threads")
    p.add_argument("--min-delay", type=float, default=MIN_DELAY_DEFAULT, help="Minimum polite delay between requests")
    p.add_argument("--max-delay", type=float, default=MAX_DELAY_DEFAULT, help="Maximum polite delay between requests")
    p.add_argument("--max-results-per-query", type=int, default=MAX_RESULTS_PER_QUERY_DEFAULT, help="Search results per query")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    if args.categories_file:
        categories = load_lines_from_file(args.categories_file)
    else:
        categories = args.categories

    seeds = load_lines_from_file(args.seeds_file) if args.seeds_file else None

    serpapi_key = args.serpapi_key or os.getenv("SERPAPI_KEY")
    bing_key = args.bing_key or os.getenv("BING_API_KEY")
    hunter_key = args.hunter_key or os.getenv("HUNTER_API_KEY")

    if args.use_hunter and not hunter_key:
        logger.warning("use-hunter requested but no hunter_key provided. Use HUNTER_API_KEY env var or --hunter-key.")
    if args.use_hunter and args.preview_hunter_costs:
        logger.info("Previewing Hunter costs (no Hunter API calls will be made).")
        harvest(
            categories,
            serpapi_key=serpapi_key,
            bing_key=bing_key,
            hunter_key=hunter_key,
            use_hunter=args.use_hunter,
            use_hunter_domain_search=args.use_hunter_domain_search,
            seeds=seeds,
            use_selenium=args.use_selenium,
            output=args.output,
            workers=args.workers,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_results_per_query=args.max_results_per_query,
            preview_hunter_costs=True,
            max_hunter_verifications=args.max_hunter_verifications,
        )
        logger.info("Preview complete. Re-run with --yes-run-hunter to actually perform Hunter verification calls.")
        return

    if args.use_hunter and not args.yes_run_hunter:
        logger.info("Hunter verification requires confirmation. Re-run with --yes-run-hunter to actually call Hunter API.")
        # still run harvest in preview-like mode
        harvest(
            categories,
            serpapi_key=serpapi_key,
            bing_key=bing_key,
            hunter_key=hunter_key,
            use_hunter=args.use_hunter,
            use_hunter_domain_search=args.use_hunter_domain_search,
            seeds=seeds,
            use_selenium=args.use_selenium,
            output=args.output,
            workers=args.workers,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_results_per_query=args.max_results_per_query,
            preview_hunter_costs=True,
            max_hunter_verifications=args.max_hunter_verifications,
        )
        logger.info("Preview only run completed. Re-run with --yes-run-hunter to perform Hunter verifications.")
        return

    # Normal run
    harvest(
        categories,
        serpapi_key=serpapi_key,
        bing_key=bing_key,
        hunter_key=hunter_key,
        use_hunter=(args.use_hunter and args.yes_run_hunter),
        use_hunter_domain_search=args.use_hunter_domain_search,
        seeds=seeds,
        use_selenium=args.use_selenium,
        output=args.output,
        workers=args.workers,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_results_per_query=args.max_results_per_query,
        preview_hunter_costs=False,
        max_hunter_verifications=args.max_hunter_verifications,
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)