import sys
from typing_extensions import Optional
from pydantic import BaseModel
import soupsieve
from pathlib import Path
import json
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
import re

import requests
from bs4 import BeautifulSoup

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Amr-Trex/flyrank-assignment#5-scraper)"
DELAY_SECONDS = 0.1

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
STATS = {
    "pages_fetched": 0,
    "cache_hits": 0,
    "failed_pages": 0,
    "invalid_records": 0
}

# this time getting iso function is for getting the current time from the system as scraper works
def now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds").replace("+00:00", "Z")

# this one below is to get the time of the file that was created using path
def file_iso(path):
    return datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=timezone.utc
    ).isoformat(timespec="seconds").replace("+00:00", "Z")


def cache_file(url):
    if "/catalogue/page-" in url:
        page = url.split("/catalogue/page-")[1].split(".html")[0]
        return CACHE_DIR / f"catalogue-page-{page}.html"

    if url.endswith("index.html"):
        slug = url.rstrip("/").split("/")[-2]
        return CACHE_DIR / f"book-{slug}.html"

    slug = url.split("//")[-1].replace("/", "-")
    return CACHE_DIR / f"page-{slug}.html"


def fetch(url):
    path = cache_file(url)

    if path.exists():
        STATS["cache_hits"] += 1
        html = path.read_text(encoding="utf-8")
        print(f"CACHE HIT {url} size={len(html)}")
        return html, file_iso(path)

    for attempt in range(2):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                print(f"RETRY {url} (network timeout/error)...")
                time.sleep(1)
                continue
            raise Exception(f"Network error: {e}")

        if response.status_code == 200:
            STATS["pages_fetched"] += 1
            html = response.text
            path.write_text(html, encoding="utf-8")
            print(f"FETCH {url} status={response.status_code} size={len(html)}")
            time.sleep(DELAY_SECONDS)
            return html, now_iso()

        elif response.status_code in [404, 403]:
            raise Exception(f"Bad status code: {response.status_code}")

        elif 500 <= response.status_code < 600:
            if attempt == 0:
                print(f"RETRY {url} (server error {response.status_code})...")
                time.sleep(1)
                continue
            raise Exception(f"Server error: {response.status_code}")
            
        else:
            raise Exception(f"Bad status code: {response.status_code}")


def discover_books():
    books = {}
    url = START_URL
    pages = 0

    while url and pages < 3:
        html, _ = fetch(url)   # time regarding when the pages were fetched is not necessary so it is discarded here
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")
            # we get the referrence link from the <a> tag (link)

            if not href:
                continue

            book_url = urljoin(url, href)
            # add to book url to the list if it doesn't exist
            if book_url not in books:
                books[book_url] = url

        # selects the element for pagination on the frontend side
        next_link = soup.select_one("li.next a")

        if next_link and next_link.get("href"):
            url = urljoin(url, next_link["href"])
        else:
            url = None

        pages += 1

    return books, pages


def clean_text(element):
    if element is None:
        return None

    text = " ".join(element.get_text().split())

    if text == "":
        return None

    return text


def rating_value(soup):
    rating_element = soup.select_one("p.star-rating")

    if rating_element is None:
        return None

    classes = rating_element.get("class", [])

    for class_name in classes:
        if class_name != "star-rating":
            return class_name

    return None


def clean_price(price_str):
    if price_str:
        match = re.search(r"[\d.]+", price_str)
        return float(match.group()) if match else None
    else:
        return None


def save_json(filename, data):
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str

def validate_record(raw_record):
    record = BookRecord(**dict(raw_record))

    if not record.product_url.startswith(("https://", "http://")):
        raise ValueError("product_url must start with https:// or http://")

    if not record.source_page.startswith(("https://", "http://")):
        raise ValueError("source_page must start with https:// or http://")

    if hasattr(record, "model_dump"):
        return record.model_dump()

    return record.dict()


def parse_book(html, product_url, source_page, fetched_at):
    soup = BeautifulSoup(html, "html.parser")

    raw_price_text = clean_text(soup.select_one("p.price_color"))

    record = {
        "title": clean_text(soup.select_one("h1")),
        "product_url": product_url,
        "price_text": raw_price_text,
        "price_gbp": clean_price(raw_price_text),
        "availability_text": clean_text(soup.select_one("p.instock.availability")),
        "rating_text": rating_value(soup),
        "description": clean_text(soup.select_one("#content_inner > article > p")),
        "source_page": source_page,
        "fetched_at": fetched_at,
    }

    required_fields = ["title", "price_text", "availability_text", "rating_text"]

    for field in required_fields:
        if record[field] is None:
            raise ValueError(f"Missing field: {field}")

    return record


if __name__ == "__main__":
    start_time = time.time()
    started_at = now_iso()
    
    books, pages = discover_books()
    
    # # TEST: injecting a fake broken URL to see if we pass the --test-broken flag
    # fake_url = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"
    # books[fake_url] = START_URL
    # print(">>> Injected fake URL for testing...")

    records = []
    errors = []

    for book_url, source_page in books.items():
        try:
            html, fetched_at = fetch(book_url)
            record = parse_book(html, book_url, source_page, fetched_at)
            records.append(validate_record(record))
        except Exception as e:
            print("Exception:", e)

            error_type = "fetch" if "status code" in str(e) or "Network error" in str(e) else "record"
            if error_type == "fetch":
                STATS["failed_pages"] += 1
            else:
                STATS["invalid_records"] += 1
                
            errors.append({
                "type": error_type,
                "url": book_url,
                "reason": str(e)
            })
            continue

    if records:
        print("Sample raw record:")
        print(json.dumps(records[0], indent=2))

    unique_records = {}
    for record in records:
        unique_records[record["product_url"]] = record

    final_records = list(unique_records.values())

    save_json("books.json", final_records)
    save_json("errors.json", errors)
    
    # STAGE 5: Write the run report
    report = {
        "started_at": started_at,
        "duration_seconds": round(time.time() - start_time, 2),
        "catalogue_pages": pages,
        "discovered_urls": len(books),
        "pages_fetched": STATS["pages_fetched"],
        "cache_hits": STATS["cache_hits"],
        "valid_records": len(final_records),
        "invalid_records": STATS["invalid_records"],
        "failed_pages": STATS["failed_pages"],
    }
    save_json("run-report.json", report)

    print(f"detail_pages={len(final_records)}")
    print(f"failed_pages={STATS['failed_pages']}")