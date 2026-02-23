# Email Harvester

Find publicly listed business emails from category keywords with a safer, testable, production-ready Python CLI.

<div align="right">

[![CI](https://github.com/SagarBiswas-MultiHAT/Email-Harvester/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SagarBiswas-MultiHAT/Email-Harvester/actions/workflows/ci.yml)
&nbsp;
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
&nbsp;
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)
&nbsp;
![Version](https://img.shields.io/badge/version-1.0.0-informational)

</div>

## Overview

Email Harvester is a command-line tool for discovering publicly visible email addresses across category-relevant websites.
It supports a fallback search chain (SerpApi -> Bing -> DuckDuckGo), polite crawling with robots.txt awareness, and optional Hunter.io enrichment/verification.
The project is designed for engineers and growth teams who need reproducible lead discovery workflows and auditable outputs.
This repository now ships as a modular Python package with linting, tests, CI, and clear contribution standards.

## Features

- Multi-backend search discovery with automatic fallback
- Polite crawling with robots.txt checks
- Contact/About link traversal and `mailto:` extraction
- Optional Hunter domain search and verification
- MX-based domain mail validation
- Deterministic quality scoring (`High`, `Medium`, `Low`)
- Backward-compatible legacy script entrypoint (`email_harvester_ultimate.py`)
- Full CI pipeline: lint -> test -> build -> dependency audit

## Demo / Screenshots

```
(.venv) PS H:\updatedReposV1\NewProjects\Email-Harvester> email-harvester --categories-file categories.txt --workers 8 --max-results-per-query 20 --output results.csv
2026-02-24 03:07:24,856 INFO Searching: intitle:"contact" "Blogger" OR intitle:"about" "Blogger" OR "Blogger" "contact"
2026-02-24 03:07:34,961 INFO  --> found 10 candidate URLs
2026-02-24 03:07:37,151 INFO Searching: "Blogger" site:.com
2026-02-24 03:07:41,754 INFO  --> found 6 candidate URLs
2026-02-24 03:07:43,617 INFO Searching: "Blogger" services
2026-02-24 03:07:58,629 WARNING Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'ReadTimeoutError("HTTPSConnectionPool(host='serpapi.com', port=443): Read timed out. (read timeout=15.0)")': /search.json?q=%22Blogger%22+services&engine=google&num=20&api_key=ebf79edb19f469b234b41f4dbca90c961d021f1fbd80c15975c0508645405b64
2026-02-24 03:08:00,540 INFO  --> found 9 candidate URLs
2026-02-24 03:08:02,146 INFO Searching: intitle:"contact" "affiliate marketer" OR intitle:"about" "affiliate marketer" OR "affiliate marketer" "contact"
2026-02-24 03:08:07,181 INFO  --> found 10 candidate URLs
2026-02-24 03:08:09,163 INFO Searching: "affiliate marketer" site:.com
2026-02-24 03:08:20,329 INFO  --> found 7 candidate URLs
2026-02-24 03:08:21,862 INFO Searching: "affiliate marketer" services
2026-02-24 03:08:30,720 INFO  --> found 10 candidate URLs
2026-02-24 03:08:31,640 INFO Total candidate URLs to scan: 50
scanning pages:   0%|                                                                                                                    | 0/50 [00:00<?, ?it/s]2026-02-24 03:08:34,134 INFO Skipping due to robots.txt: https://medium.com/@markjenkins/how-to-contact-and-work-with-bloggers-to-promote-your-product-d9eccb51ab11
scanning pages:   2%|██▏                                                                                                         | 1/50 [00:02<01:53,  2.31s/it]2026-02-24 03:08:36,409 INFO Skipping due to robots.txt: https://www.terrieragency.com/blogger-outreach-finding-contact-vloggers/
scanning pages:   4%|████▎                                                                                                       | 2/50 [00:04<01:49,  2.29s/it]2026-02-24 03:08:36,450 INFO Skipping due to robots.txt: https://webapps.stackexchange.com/questions/11097/how-to-add-a-contact-me-form-to-a-blog-hosted-on-blogger
scanning pages:  10%|██████████▊                                                                                                 | 5/50 [00:08<01:16,  1.69s/it]2026-02-24 03:08:41,452 INFO Skipping due to robots.txt: https://contactout.com/
scanning pages:  16%|█████████████████▎                                                                                          | 8/50 [00:10<00:42,  1.01s/it]2026-02-24 03:08:42,414 INFO Skipping due to robots.txt: https://www.sciencedirect.com/topics/computer-science/blogger
scanning pages:  20%|█████████████████████▍                                                                                     | 10/50 [00:12<00:36,  1.09it/s]2026-02-24 03:08:44,049 INFO Skipping due to robots.txt: https://www.bloggeroutreach.io/
scanning pages:  22%|███████████████████████▌                                                                                   | 11/50 [00:12<00:28,  1.35it/s]2026-02-24 03:08:44,273 INFO Skipping due to robots.txt: https://en.wikipedia.org/wiki/Blogger_(service)
scanning pages:  30%|████████████████████████████████                                                                           | 15/50 [00:15<00:27,  1.26it/s]2026-02-24 03:08:47,037 INFO Skipping due to robots.txt: https://www.reddit.com/r/seo_saas/comments/1i1vhp8/anyone_had_success_with_a_quality_blogger/
scanning pages:  34%|████████████████████████████████████▍                                                                      | 17/50 [00:15<00:15,  2.07it/s]2026-02-24 03:08:47,166 INFO Skipping due to robots.txt: https://www.thehoth.com/blogger/
scanning pages:  36%|██████████████████████████████████████▌                                                                    | 18/50 [00:15<00:12,  2.52it/s]2026-02-24 03:08:49,279 INFO Skipping due to robots.txt: https://www.affiliatemarketertraining.com/contact-us/
scanning pages:  38%|████████████████████████████████████████▋                                                                  | 19/50 [00:17<00:25,  1.20it/s]2026-02-24 03:08:49,363 INFO Skipping due to robots.txt: https://www.quora.com/How-do-I-contact-affiliate-marketers
scanning pages:  42%|████████████████████████████████████████████▉                                                              | 21/50 [00:17<00:16,  1.71it/s]2026-02-24 03:08:50,298 INFO Skipping due to robots.txt: https://missyward.com/contact/
scanning pages:  44%|███████████████████████████████████████████████                                                            | 22/50 [00:18<00:16,  1.74it/s]2026-02-24 03:08:54,640 INFO Skipping due to robots.txt: https://cupofjo.com/about/
2026-02-24 03:08:54,736 INFO Skipping due to robots.txt: https://rocketreach.co/affiliate-marketer-email_265244435
scanning pages:  50%|█████████████████████████████████████████████████████▌                                                     | 25/50 [00:25<00:34,  1.37s/it]2scanning pages:  44%|███████████████████████████████████████████████                                                            | 22/50 [00:18<00:16,  1.74it/s]2026-02-24 03:08:54,640 INFO Skipping due to robots.txt: https://cupofjo.com/about/
2026-02-24 03:08:54,736 INFO Skipping due to robots.txt: https://rocketreach.co/affiliate-marketer-email_265244435
scanning pages:  50%|█████████████████████████████████████████████████████▌                                                     | 25/50 [00:25<00:34,  1.37s/it]22026-02-24 03:08:54,736 INFO Skipping due to robots.txt: https://rocketreach.co/affiliate-marketer-email_265244435
scanning pages:  50%|█████████████████████████████████████████████████████▌                                                     | 25/50 [00:25<00:34,  1.37s/it]2026-02-24 03:08:57,739 INFO Skipping due to robots.txt: https://www.instagram.com/p/DUidEv8iaTL/
scanning pages:  52%|███████████████████████████████████████████████████████▋                                                   | 26/50 [00:25<00:29,  1.23s/it]2026-02-24 03:08:57,739 INFO Skipping due to robots.txt: https://www.instagram.com/p/DUidEv8iaTL/
scanning pages:  52%|███████████████████████████████████████████████████████▋                                                   | 26/50 [00:25<00:29,  1.23s/it]2026-02-24 03:08:57,813 INFO Skipping due to robots.txt: https://www.facebook.com/groups/nzfacamping/posts/1690150319029644/
scanning pages:  58%|██████████████████████████████████████████████████████████████                                             | 29/50 [00:26<00:13,  1.52it/s]2026-02-24 03:08:58,366 WARNING Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.affiliatemarketer.wuaze.com'. (_s026-02-24 03:08:57,813 INFO Skipping due to robots.txt: https://www.facebook.com/groups/nzfacamping/posts/1690150319029644/
scanning pages:  58%|██████████████████████████████████████████████████████████████                                             | 29/50 [00:26<00:13,  1.52it/s]2026-02-24 03:08:58,366 WARNING Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.affiliatemarketer.wuaze.com'. (_ssl.c:1081)"))': /__trashed/
2026-02-24 03:08:59,335 INFO Skipping due to robots.txt: https://www.locationrebel.com/how-to-start-affiliate-marketing/
sl.c:1081)"))': /__trashed/
2026-02-24 03:08:59,335 INFO Skipping due to robots.txt: https://www.locationrebel.com/how-to-start-affiliate-marketing/
2026-02-24 03:08:59,335 INFO Skipping due to robots.txt: https://www.reddit.com/r/passive_income/comments/irkcl9/what_is_affiliate_marketing/
2026-02-24 03:08:59,335 INFO Skipping due to robots.txt: https://www.reddit.com/r/passive_income/comments/irkcl9/what_is_affiliate_marketing/
scanning pages:  60%|████████████████████████████████████████████████████████████████▏                                          | 30/50 [00:27<00:14,  1.35it/s]2026-02-24 03:09:00,848 WARNING Retrying (Retry(total=1, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerific026-02-24 03:09:00,848 WARNING Retrying (Retry(total=1, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.affiliatemarketer.wuaze.com'. (_ssl.c:1081)"))': /__trashed/
sl.c:1081)"))': /__trashed/
scanning pages:  64%|████████████████████████████████████████████████████████████████████▍                                      | 32/50 [00:29<00:14,  1.28it/s]2026-02-24 03:09:01,056 INFO Skipping due to robots.txt: https://www.indeed.com/career-advice/finding-a-job/how-to-become-affiliate-marketer
026-02-24 03:09:01,056 INFO Skipping due to robots.txt: https://www.indeed.com/career-advice/finding-a-job/how-to-become-affiliate-marketer
scanning pages:  72%|█████████████████████████████████████████████████████████████████████████████                              | 36/50 [00:31<00:08,  1.70it/s]2scanning pages:  72%|█████████████████████████████████████████████████████████████████████████████                              | 36/50 [00:31<00:08,  1.70it/s]2026-02-24 03:09:03,996 INFO Skipping due to robots.txt: https://impact.com/
scanning pages:  74%|███████████████████████████████████████████████████████████████████████████████▏                           | 37/50 [00:32<00:08,  1.50it/s]2026-02-24 03:09:04,362 WARNING Retrying (Retry(total=0, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.affiliatemarketer.wuaze.com'. (_ssl.c:1081)"))': /__trashed/
scanning pages:  76%|█████████████████████████████████████████████████████████████████████████████████▎                         | 38/50 [00:33<00:09,  1.31it/s]2026-02-24 03:09:05,167 INFO Skipping due to robots.txt: https://powerdigitalmarketing.com/services/affiliate-marketing/
scanning pages:  78%|███████████████████████████████████████████████████████████████████████████████████▍                       | 39/50 [00:33<00:06,  1.69it/s]2026-02-24 03:09:05,286 INFO Skipping due to robots.txt: https://www.accelerationpartners.com/
scanning pages: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:43<00:00,  1.16it/s] 
2026-02-24 03:09:14,894 INFO Unique emails found on pages: 71
2026-02-24 03:09:32,390 INFO Wrote results to results.csv
```

## Quick Start

### Prerequisites

- Python `3.10` to `3.13`
- `pip` (latest recommended)

### Installation

```bash
git clone https://github.com/SagarBiswas-MultiHAT/Email-Harvester.git
cd Email-Harvester
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Optional Selenium support:

```bash
python -m pip install -e .[selenium]
```

### Run the Project

Run with categories file:

```bash
email-harvester --categories-file categories.txt --output results.csv
```

Or run with inline categories:

```bash
email-harvester --categories "SEO Agency" "Affiliate Marketer" --output results.csv
```

You should see progress output, followed by a message similar to:

```text
INFO Wrote results to results.csv
```

## Usage / Examples

### 1) Free Mode (No API Keys)

```bash
email-harvester --categories-file categories.txt --workers 8 --max-results-per-query 20 --output results.csv
```

Uses DuckDuckGo fallback and MX checks only.

### 2) SerpApi Discovery Mode (Higher Recall)

```bash
export SERPAPI_KEY="your_key"
email-harvester --categories-file categories.txt --serpapi-key "$SERPAPI_KEY" --max-results-per-query 30 --output serpapi_results.csv
```

Uses SerpApi as the primary search backend, then falls back to Bing and DuckDuckGo if needed.

### 3) Hunter Preview Mode (No Credits Spent)

```bash
email-harvester --categories-file categories.txt --use-hunter --preview-hunter-costs --output preview.csv
```

Shows estimated verification scope without executing Hunter verification calls.

### 4) Hunter Verified Mode

```bash
export HUNTER_API_KEY="your_key"
email-harvester --categories-file categories.txt --use-hunter --yes-run-hunter --max-hunter-verifications 40 --output verified.csv
```

Performs real Hunter verifications up to the configured cap.

### 5) Seeds-Only Mode (Skip Search)

Create `seeds.txt` with one URL per line:

```text
https://example.com
https://another-example.com
```

Then run:

```bash
email-harvester --seeds-file seeds.txt --output seeded.csv
```

This bypasses search providers and crawls only your supplied URLs.

## Project Structure

```text
Email-Harvester/
|- src/email_harvester/
|  |- cli.py                 # CLI parser and command entrypoint
|  |- config.py              # Validated runtime config model
|  |- pipeline.py            # Main orchestration flow
|  |- search_backends.py     # SerpApi/Bing/DDG fallback logic
|  |- fetchers.py            # Requests/Selenium fetch layers
|  |- extraction.py          # Email and contact link extraction
|  |- hunter.py              # Hunter API client
|  |- scoring.py             # Quality scoring logic
|  |- validation.py          # Input/runtime guards and MX checks
|  `- io_csv.py              # CSV schema and writing
|- tests/                    # Unit and integration-style tests
|- .github/workflows/ci.yml  # GitHub Actions pipeline
|- pyproject.toml            # Build metadata + tooling config
|- Makefile                  # Common developer commands
|- Dockerfile                # Containerized CLI runtime
`- email_harvester_ultimate.py # Legacy wrapper entrypoint
```

## Running Tests

Run all tests with coverage:

```bash
python -m pytest
```

Run lint checks:

```bash
python -m ruff check src tests
python -m ruff format --check src tests
```

Run type checks:

```bash
python -m mypy src/email_harvester
```

Coverage is enforced at `>=85%` in CI.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, quality gates, and pull request expectations.

## Roadmap

- [ ] Add opt-in async crawler for higher throughput
- [ ] Add richer output formats (`jsonl`, `parquet`)
- [ ] Add per-domain rate-limiting profiles
- [ ] Add first-party OpenAPI-compatible service mode
- [ ] Add benchmark suite for crawl/search performance tracking

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

Built with open-source tools including `requests`, `BeautifulSoup`, `dnspython`, `pytest`, and `ruff`.
