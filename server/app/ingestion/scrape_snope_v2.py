# server/app/ingestion/scrape_snope_v2.py

import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.services.embedding_service import get_embedding
from app.services.db_service import insert_claim_with_vector

from app.config import REQUEST_TIMEOUT, SLEEP_BETWEEN_REQUESTS, MAX_RETRIES

BASE_ARCHIVE = "https://www.snopes.com/fact-check/?pagenum={}"
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
    """GET with basic retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            # 4xx other than 429: likely permanent for this URL
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                print(f"[WARN] {resp.status_code} for {url}")
                return resp
            # 5xx or 429: retry
            backoff = 0.5 * attempt
            print(f"[WARN] {resp.status_code} for {url}, retrying in {backoff:.1f}s...")
            time.sleep(backoff)
        except requests.RequestException as e:
            backoff = 0.75 * attempt
            print(f"[WARN] Request error on {url}: {e} (retry {attempt}/{MAX_RETRIES})")
            time.sleep(backoff)
    return None

def _soup(url):
    resp = _fetch(url)
    if not resp:
        return None
    return BeautifulSoup(resp.text, "html.parser")

def _extract_archive_links(soup: BeautifulSoup):
    """
    Robustly find fact-check article links on the archive page.
    We avoid brittle class names by looking for h2 > a within article cards.
    """
    links = set()

    # Primary: <article> cards with <h2><a>
    for a in soup.select("a.outer_article_link_wrapper"):
        href = a.get("href", "").strip()
        if href:
            links.add(href)

    # Fallbacks: sometimes listings use div-based cards
    if not links:
        for a in soup.select("h2.title a[href], .list-post h2 a[href]"):
            href = a.get("href")
            if href:
                links.add(href)

    # Filter to fact-check paths just in case
    links = {u for u in links if "/fact-check/" in u}
    return sorted(links)


def _parse_iso_date(soup: BeautifulSoup):
    # Prefer OpenGraph/Article meta
    meta = soup.select_one('meta[property="article:published_time"]')
    if meta and meta.has_attr("content"):
        return meta["content"].strip()
    # Fallback: <time datetime="...">
    t = soup.select_one("time[datetime]")
    if t and t.has_attr("datetime"):
        return t["datetime"].strip()
    # Last resort: visible date text (less reliable)
    t2 = soup.select_one("time")
    if t2 and t2.get_text(strip=True):
        return t2.get_text(strip=True)
    return None


def _parse_verdict(soup: BeautifulSoup):
    """
    Prefer the explicit rating text block or the img alt.
    We store raw verdict exactly as Snopes presents it.
    """
    # e.g., <div class="rating_title_wrap">Incorrect Attribution</div>
    vt = soup.select_one(".rating_title_wrap")
    if vt:
        # Get only the text that is a direct child of the div, ignoring other tags
        direct_text = "".join(vt.find_all(string=True, recursive=False)).strip()
        if direct_text:
            return direct_text

    # e.g., <div class="rating_img_wrap"><img alt="Incorrect Attribution" /></div>
    img = soup.select_one(".rating_img_wrap img[alt]")
    if img and img.has_attr("alt") and img["alt"].strip():
        return img["alt"].strip()

    # Older/other variants
    alt = soup.select_one(".media-rating, .media-badge")
    if alt and alt.get_text(strip=True):
        return alt.get_text(strip=True)

    return "Unverified"


def _parse_claim_text(soup: BeautifulSoup):
    # Most reliable: article H1
    h1 = soup.select_one("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    # Fallbacks
    t = soup.select_one(".claim_cont, header h1, .title")
    if t and t.get_text(strip=True):
        return t.get_text(strip=True)

    return None


def scrape_article(url: str):
    s = _soup(url)
    if not s:
        return None

    claim = _parse_claim_text(s)
    verdict = _parse_verdict(s)
    date_iso = _parse_iso_date(s)

    return {
        "claim": claim,
        "verdict": verdict,
        "source_url": url,
        "date": date_iso,
    }


def scrape_snopes(start_page: int, max_pages: int | None = None):
    page = start_page
    total_inserted = 0
    seen_urls = set()

    while True:
        if max_pages is not None and page >= start_page + max_pages:
            print(f"[DONE] Reached max_pages at page {page}.")
            break

        archive_url = BASE_ARCHIVE.format(page)
        print(f"\n=== Scraping Snopes archive page {page}: {archive_url}")
        soup = _soup(archive_url)
        if not soup:
            print("[STOP] Could not load archive page.")
            break

        links = _extract_archive_links(soup)
        if not links:
            print("[STOP] No article links found on this page. Assuming end of archive.")
            break

        print(f"Found {len(links)} article links.")

        for idx, url in enumerate(links, start=1):
            if url in seen_urls:
                continue
            seen_urls.add(url)

            print(f"  [{idx:02d}/{len(links)}] Article → {url}")
            data = scrape_article(url)
            time.sleep(SLEEP_BETWEEN_REQUESTS)

            if not data:
                print("    [SKIP] Failed to scrape article.")
                continue

            claim = data["claim"]
            verdict = data["verdict"]
            source_url = data["source_url"]
            date_iso = data["date"]

            if not claim:
                print("    [SKIP] No claim (H1) found.")
                continue

            try:
                if insert_claim_with_vector(
                    text=claim,
                    verdict=verdict,
                    source_url=source_url,
                    short_points=None,  # Snopes doesn't have short points
                    date=date_iso
                ):
                    total_inserted += 1
                    print(f"    [OK] Inserted → verdict='{verdict}' date='{date_iso}'")
                else:
                    print(f"    [SKIP] Duplicate or failed insert for {source_url}")
                    sys.exit(0)

            except Exception as e:
                print(f"    [ERR] Qdrant insert failed: {e}")

        # small pause between archive pages
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        page += 1

    print(f"\n[SUMMARY] Inserted {total_inserted} articles total.")


if __name__ == "__main__":
    # Set max_pages=None to run until the archive ends.
    scrape_snopes(start_page=1, max_pages=2)
