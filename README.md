# 🚀 Email Harvester Ultimate

Production-ready email harvesting tool with:

* Multi-backend search (SerpApi → Bing → DuckDuckGo fallback)
* Polite crawling with robots.txt support
* Contact/About link discovery
* Mailto extraction
* Optional Selenium for JavaScript-heavy sites
* Hunter.io integration (domain search + verification)
* MX record validation
* Deduplication
* Quality scoring (High / Medium / Low)
* Threaded crawling with rate control
* Safe Hunter credit preview mode

This project is designed to be **powerful, controlled, and production-safe**.

Main file:

```bash
email_harvester_ultimate.py
```

---

# 📌 What This Tool Actually Does

Given a list of categories like:

* SEO Agency
* Google Ads Specialist
* Affiliate Marketer
* Media Buyer

The script will:

1. Generate smart search queries
2. Discover candidate websites
3. Crawl pages politely (respecting robots.txt)
4. Follow contact/about links
5. Extract visible emails
6. Optionally enrich results via Hunter domain search
7. Optionally verify emails via Hunter verifier
8. Validate domains via MX check
9. Rank emails by quality
10. Export everything to CSV

---

# 🧠 How Search Works

Search backend priority:

1. SerpApi (if provided)
2. Bing Web Search API (if provided)
3. DuckDuckGo HTML fallback (free, no key required)

This means:

* You can run it 100% free
* Or you can upgrade discovery accuracy using paid APIs

---

# 📦 Installation

## Required

```bash
pip install requests beautifulsoup4 dnspython tqdm
```

## Optional (Selenium support)

```bash
pip install selenium webdriver-manager
```

---

# 🗂 File Structure

```
project/
│
├── email_harvester_ultimate.py
├── categories.txt
├── verified_ranked.csv
```

---

# 📝 categories.txt Example

```
SEO Agency
SEO Expert
Facebook Ads Agency
Google Ads Specialist
Affiliate Marketer
Email Marketing Agency
Funnel Builder
Media Buyer
```

One category per line.
No quotes needed.

---

# ⚙️ CLI Options Explained

## Required (choose one)

### `--categories`

Provide categories directly in CLI.

Example:

```bash
--categories "SEO Agency" "Media Buyer"
```

### `--categories-file`

Load categories from file.

Example:

```bash
--categories-file categories.txt
```

---

## Optional Search Keys

### `--serpapi-key`

Improves Google search discovery.

### `--bing-key`

Alternative to SerpApi.

If neither is provided → DuckDuckGo is used automatically.

---

## Hunter Integration

### `--use-hunter`

Enable email verification via Hunter.

### `--hunter-key`

Hunter API key (or use environment variable).

### `--use-hunter-domain-search`

Fetch emails directly from Hunter per domain.

### `--preview-hunter-costs`

Show how many verifications would be used, without spending credits.

### `--max-hunter-verifications`

Limit number of verification calls.

### `--yes-run-hunter`

Safety confirmation before actually calling Hunter.

---

## Selenium

### `--use-selenium`

Use headless Chrome for JavaScript-heavy sites.

Slower, but useful for dynamic websites.

---

## Performance Controls

### `--workers`

Number of parallel threads.

### `--min-delay`

Minimum polite delay between requests.

### `--max-delay`

Maximum polite delay.

### `--max-results-per-query`

Search results per query.

---

# 📊 Output CSV Columns

| Column            | Meaning                    |
| ----------------- | -------------------------- |
| email             | Extracted email            |
| first_seen_source | First URL where found      |
| all_sources       | All URLs where found       |
| domain            | Source domain              |
| mx_ok             | MX record valid            |
| hunter_result     | Hunter verification result |
| hunter_confidence | Hunter confidence score    |
| quality           | High / Medium / Low        |
| date_scraped_utc  | Timestamp                  |
| notes             | Extraction source type     |

---

# 🏆 Quality Scoring Logic

High if:

* Hunter says deliverable
  OR
* Hunter confidence ≥ 80
  OR
* MX valid and found multiple times

Medium if:

* MX valid but weak Hunter score

Low if:

* No MX and no verification

---

# 🟢 BEST COMMANDS (10/10 Production Setup)

## 🔹 1. Free Mode (No API Keys)

```bash
python email_harvester_ultimate.py \
--categories-file categories.txt \
--workers 10 \
--max-results-per-query 25 \
--output results.csv
```

Good for:

* Testing
* Budget mode
* Basic harvesting

---

## 🔹 2. Best Discovery Mode (SerpApi + Hunter + Ranking)

Set environment variables (recommended):

Windows:

```powershell
setx SERPAPI_KEY "your_serpapi_key"
setx HUNTER_API_KEY "your_hunter_key"
```

Linux/macOS:

```bash
export SERPAPI_KEY="your_serpapi_key"
export HUNTER_API_KEY="your_hunter_key"
```

Then run:

```bash
python email_harvester_ultimate.py \
--categories-file categories.txt \
--use-hunter \
--use-hunter-domain-search \
--yes-run-hunter \
--max-hunter-verifications 40 \
--max-results-per-query 30 \
--workers 12 \
--min-delay 0.8 \
--max-delay 2.5 \
--output verified_ranked.csv
```

This gives:

* Broad search coverage
* Domain enrichment
* Hunter verification
* Quality ranking
* Production-grade output

This is your **true 10/10 command**.

---

## 🔹 3. Safe Hunter Preview Mode

```bash
python email_harvester_ultimate.py \
--categories-file categories.txt \
--use-hunter \
--preview-hunter-costs \
--output preview.csv
```

No credits are used.

---

## 🔹 4. Selenium Mode (Dynamic Sites)

```bash
python email_harvester_ultimate.py \
--categories-file categories.txt \
--use-selenium \
--workers 6 \
--output selenium_results.csv
```

Use only if necessary.

---

# ⚡ Performance Tuning Guide

| Goal                | Setting                            |
| ------------------- | ---------------------------------- |
| Faster              | Increase `--workers`               |
| Safer               | Increase delays                    |
| More discovery      | Increase `--max-results-per-query` |
| Save Hunter credits | Lower `--max-hunter-verifications` |

---

# 🔐 Security Best Practices

* Never paste API keys in public logs
* Use environment variables
* Regenerate keys if exposed
* Start with `--preview-hunter-costs`

---

# 🧩 Seeds Mode (Advanced)

If you already have URLs:

```
--seeds-file seeds.txt
```

This skips searching and directly crawls those URLs.

---

# 📈 Example Real Production Flow

Step 1:
Free discovery

```bash
--output raw.csv
```

Step 2:
Filter High-quality domains

Step 3:
Run Hunter only on filtered emails

This reduces credit waste.

---

# 🎯 When To Use What

| Situation      | Recommended Setup    |
| -------------- | -------------------- |
| Testing        | Free mode            |
| Client leads   | SerpApi + Hunter     |
| JS-heavy sites | Selenium             |
| Tight budget   | DuckDuckGo + MX only |

---

# 🧠 Why This Tool Is Different

* Respects robots.txt
* Multi-backend failover
* Hunter preview safety
* Threaded but rate-limited
* Domain-level enrichment
* Quality scoring system
* Structured CSV export

It is not just a scraper.
It is a controlled, production-ready lead intelligence pipeline.

---

# 📜 License & Responsibility

Use responsibly.

Comply with:

* Website terms of service
* Local data regulations
* Email marketing laws (e.g., CAN-SPAM, GDPR)

This tool extracts publicly visible information.
You are responsible for how you use it.

---

# 🔥 Final Words

If configured properly with:

* SerpApi
* Hunter verification
* Domain search
* Optimized threading
* Controlled delays

This becomes a professional-grade email harvesting system capable of generating high-quality, ranked lead lists.

---
