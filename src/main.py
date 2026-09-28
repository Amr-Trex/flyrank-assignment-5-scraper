from pathlib import Path
import requests
import time

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Amr-Trex/flyrank-assignment#5-scraper)"

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def fetch_page_one():
    path = CACHE_DIR / "catalogue-page-1.html"

    if path.exists():
        html = path.read_text(encoding="utf-8")
        print(f"CACHE HIT {START_URL} size={len(html)}")
        return html

    response = requests.get(
        START_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"Bad status code: {response.status_code}")

    html = response.text
    path.write_text(html, encoding="utf-8")

    print(f"FETCH {START_URL} status={response.status_code} size={len(html)}")

    time.sleep(0.6)
    return html


if __name__ == "__main__":
    fetch_page_one()