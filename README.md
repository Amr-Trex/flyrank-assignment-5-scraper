# The Polite Scraper

FlyRank W5 A9 scraping assignment.

This project politely scrapes the first three catalogue pages from Books to Scrape, visits all 60 linked book pages, extracts raw data, normalizes it, validates it with a schema, stores clean JSON, and writes an honest run report.


## Target classification

- Site: https://books.toscrape.com/
- Why this site: Books to Scrape is a public sandbox made for practicing scraping.
- Scope: only the first 3 catalogue pages and their 60 linked book pages.
- Data collected: title, product URL, price text, cleaned price, availability text, rating text, description, source page, and fetched timestamp.
- robots.txt result: 404 Not Found
- I will not reuse this code on another site without checking its rules and terms first.

## Lane

```
Python
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
# Activate the virtual environment
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Run the scraper:

```bash
python src/main.py
```

## Record Schema

```json
{
  "title": "string",
  "product_url": "string (must start with http/https)",
  "price_text": "string",
  "price_gbp": "float",
  "availability_text": "string",
  "rating_text": "string",
  "description": "string | null",
  "source_page": "string (must start with http/https)",
  "fetched_at": "string (ISO 8601 timestamp)"
}
```

## Politeness Rules Followed

- **User-Agent**: `FlyRankInternship-A9/1.0 (+https://github.com/Amr-Trex/flyrank-assignment#5-scraper)` to identify the bot properly.
- **Delay**: 0.1 seconds delay between requests to not overwhelm the server.
- **Timeout**: 10 seconds timeout to not hang the scraper on slow connections.
- **Cache**: Successful responses are cached locally to avoid re-fetching pages during subsequent runs.

## Honest Limitation

The scraper strictly relies on the specific HTML structure and CSS selectors of Books to Scrape. If the site's layout changes, the parsing logic will break and fail to extract the required data.

## Run Report

```json
{
  "started_at": "2026-09-30T09:17:01Z",
  "duration_seconds": 2.5,
  "catalogue_pages": 3,
  "discovered_urls": 61,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

## Why No Browser?

The data is already in the HTML that the server sends, so a browser would only add cost.

## Ethics Note

Use an official API when one exists; never bypass logins, paywalls, or blocks; collect only what you need.
