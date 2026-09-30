from pathlib import Path
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Amr-Trex/flyrank-assignment#5-scraper)"
DELAY_SECONDS = 0.7

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


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
        html = path.read_text(encoding="utf-8")
        print(f"CACHE HIT {url} size={len(html)}")
        return html

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"Bad status code: {response.status_code}")

    html = response.text
    path.write_text(html, encoding="utf-8")

    print(f"FETCH {url} status={response.status_code} size={len(html)}")

    time.sleep(DELAY_SECONDS)

    return html


def discover_books():
    books = {}
    url = START_URL
    pages = 0

    while url and pages < 3:
        html = fetch(url)
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


if __name__ == "__main__":
    books, pages = discover_books()

    print(
        f"catalogue_pages={pages} "
        f"discovered books={len(books)} "
        f"unique_urls={len(books)}"
    )