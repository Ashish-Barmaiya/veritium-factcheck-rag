# server/app/ingestion/scrape_politifact_v1.py

import sys
from dateutil import parser
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.services.embedding_service import get_embedding
from app.services.db_service import insert_claim_with_vector

from app.config import REQUEST_TIMEOUT, SLEEP_BETWEEN_REQUESTS, MAX_RETRIES

BASE_ARCHIVE = "https://www.politifact.com/factchecks/?page={}"
BASE_URL = "https://www.politifact.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = REQUEST_TIMEOUT
SLEEP_BETWEEN_REQUESTS = SLEEP_BETWEEN_REQUESTS
MAX_RETRIES = MAX_RETRIES

def _fetch(url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                print(f"[WARN] {resp.status_code} for {url}")
                return resp
            backoff = 0.5 * attempt
            print(f"[WARN] {resp.status_code} for {url}, retrying {backoff:.1f}s…")
            time.sleep(backoff)
        except requests.RequestException as e:
            backoff = 0.75 * attempt
            print(f"[WARN] Request error {url}: {e} (retry {attempt}/{MAX_RETRIES})")
            time.sleep(backoff)
    return None

def _soup(url):
    resp = _fetch(url)
    if not resp:
        return None
    return BeautifulSoup(resp.text, "html.parser") if resp else None

def _extract_archive_links(soup: BeautifulSoup):
    links = []
    for a in soup.select("div.m-statement__quote a[href]"):
        href = a.get("href")
        if href and "/factchecks/" in href:
            links.append(urljoin(BASE_URL, href))
    return links

def _parse_claim(soup: BeautifulSoup):
    h1 = soup.select_one("h1.c-title")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    q = soup.select_one("div.m-statement__quote")
    if q and q.get_text(strip=True):
        return q.get_text(strip=True)
    return None


def _parse_verdict(soup: BeautifulSoup):
    # PolitiFact usually encodes verdict in alt text of ruling image
    img = soup.select_one("img[alt][src*='meter']")
    if img and img.has_attr("alt"):
        return img["alt"].strip()

    # Or in class name of article (m-statement--true / false etc.)
    art = soup.select_one("article.m-statement")
    if art:
        classes = art.get("class", [])
        for c in classes:
            if c.startswith("m-statement--"):
                return c.replace("m-statement--", "").capitalize()
    return "Unverified"


def _parse_date(soup: BeautifulSoup):
    d = soup.select_one("span.m-author__date")
    if d:
        date_str = d.get_text(strip=True)
        try:
            parsed_date = parser.parse(date_str)
            return parsed_date.isoformat()
        except Exception as e:
            print(f"Failed to parse date: {date_str}, error: {e}")
            return None
    return None


def _parse_short_on_time(soup: BeautifulSoup):
    points = []
    for li in soup.select(".short-on-time li"):
        text = li.get_text(" ", strip=True)
        if text:
            points.append(text)
    return points


def scrape_article(url: str):
    s = _soup(url)
    if not s:
        return None
    return {
        "claim": _parse_claim(s),
        "verdict": _parse_verdict(s),
        "date": _parse_date(s),
        "short_points": _parse_short_on_time(s),
        "source_url": url,
    }


def scrape_politifact(start_page=int, max_pages=int):
    page = start_page
    total_inserted = 0
    seen = set()

    while True:
        if max_pages and page > start_page + max_pages - 1:
            break

        archive_url = BASE_ARCHIVE.format(page)
        print(f"\n=== Archive page {page}: {archive_url}")
        soup = _soup(archive_url)
        if not soup:
            break

        links = _extract_archive_links(soup)
        if not links:
            print("No links, stopping.")
            break

        for url in links:
            if url in seen:
                continue
            seen.add(url)

            print(f" → Article {url}")
            data = scrape_article(url)
            time.sleep(SLEEP_BETWEEN_REQUESTS)

            if not data or not data["claim"]:
                continue

            try:
                if insert_claim_with_vector(
                    text=data["claim"],
                    verdict=data["verdict"],
                    source_url=data["source_url"],
                    short_points=data["short_points"],
                    date=data["date"]
                ):
                    total_inserted += 1
                    print(f"   [OK] {data['verdict']} | {data['date']}")
                else:
                    print(f"   [SKIP] Duplicate {url}")
                    sys.exit(0)
            except Exception as e:
                print(f"   [ERR] DB insert failed: {e}")

        page += 1
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"\n[SUMMARY] Inserted {total_inserted} articles.")


if __name__ == "__main__":
    scrape_politifact(start_page=1, max_pages=2)
