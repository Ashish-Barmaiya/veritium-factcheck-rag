# server/app/ingestion/scrape_boomlive_v1.py

import sys
import time
import logging
import re  # Import re for regular expressions
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import bs4
from datetime import datetime
import spacy

from app.services.db_service import insert_claim_with_vector_v2, Session
from app.models import ScraperRuns, ClaimModel, Source
from app.config import REQUEST_TIMEOUT, SLEEP_BETWEEN_REQUESTS, MAX_RETRIES

# --- Configuration ---
BASE_ARCHIVE = "https://www.boomlive.in/fact-check/{}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )
}
SCRAPER_NAME = "boomlive_fact_checks"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Spacy NLP Model (Load once) ---
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("Spacy NLP model loaded successfully.")
except OSError:
    logger.error("Spacy model 'en_core_web_sm' not found. Please install it using `python -m spacy download en_core_web_sm`")
    nlp = None


# --- Scraper Helper Functions ---

def _fetch(url):
    """GET with basic retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                logger.warning(f"{resp.status_code} for {url}")
                return resp
            backoff = 0.5 * attempt
            logger.warning(f"{resp.status_code} for {url}, retrying in {backoff:.1f}s...")
            time.sleep(backoff)
        except requests.RequestException as e:
            backoff = 0.75 * attempt
            logger.warning(f"Request error on {url}: {e} (retry {attempt}/{MAX_RETRIES})")
            time.sleep(backoff)
    return None

def _soup(url):
    resp = _fetch(url)
    if not resp:
        return None
    return BeautifulSoup(resp.text, "html.parser")


def _extract_archive_links(soup: BeautifulSoup):
    """
    Extract article links from the BoomLive archive page.
    Looks for links with href starting with '/fact-check/' within common container elements.
    """
    links = set()

    # --- More Robust Link Finding ---
    # Focus on common container classes observed or likely ones
    container_selectors = [
        "div.boom-item",      # Structure 1 from your image
        "div.boom-item3",     # Structure 2 from your image
        "div.card",           # Generic card class often used
        "div.post",           # Generic post class
        "div.article",        # Generic article class
        "div.story",          # Generic story class
        "li"                  # Sometimes articles are in list items
        # Removed invalid wildcard selectors like "div.col-*"
    ]

    for selector in container_selectors:
        containers = soup.select(selector)
        for container in containers:
            # Find <a> tags directly or indirectly inside the container
            # that have an href starting with /fact-check/
            article_links = container.select("a[href^='/fact-check/']")
            for link in article_links:
                href = link.get("href", "").strip()
                if href:
                    # Make sure it's an absolute URL
                    full_url = urljoin("https://www.boomlive.in", href)
                    # Validate URL pattern: base + slug (no trailing slash, no extra path like /page/X)
                    # This regex checks for the base + a slug (non-empty path segment)
                    if re.match(r'^https://www\.boomlive\.in/fact-check/[^/]+$', full_url):
                         links.add(full_url)
    
    # --- Fallback: Find *any* link with the fact-check prefix if containers failed ---
    # This is the least specific but might catch links if container logic is completely off
    if not links:
        logger.info("No links found using container-based search, trying global search...")
        all_fact_check_links = soup.select("a[href^='/fact-check/']")
        for link in all_fact_check_links:
             href = link.get("href", "").strip()
             if href:
                 full_url = urljoin("https://www.boomlive.in", href)
                 # Again, try to match the pattern of an article page (ends without trailing slash or has slug)
                 # This regex checks for the base + a slug (non-empty path segment)
                 if re.match(r'^https://www\.boomlive\.in/fact-check/[^/]+$', full_url):
                     # Avoid obvious non-article links if possible (e.g., containing 'page', 'category')
                     # This is heuristic
                     # Check if 'page' or 'category' is in the path part of the URL
                     from urllib.parse import urlparse
                     parsed_url = urlparse(full_url)
                     path_lower = parsed_url.path.lower()
                     if '/page/' not in path_lower and '/category/' not in path_lower:
                         links.add(full_url)
    
    if not links:
        logger.warning("Still no links found after global search. Please check the HTML structure or if the page is empty.")
        # Log the title or a snippet of the page to help debugging
        page_title = soup.title.string if soup.title else "No Title"
        logger.debug(f"Page title: {page_title}")
        logger.debug(f"Page URL was: https://www.boomlive.in/fact-check/1")
    else:
        logger.info(f"Found {len(links)} links using robust/fallback methods.")

    return sorted(list(links)) # Return a sorted list


def _parse_iso_date(soup: BeautifulSoup):
    """
    Extracts the ISO date from the article.
    Looks for OpenGraph meta tag first, then <time> tags.
    """
    meta = soup.select_one('meta[property="article:published_time"]')
    if meta and meta.has_attr("content"):
        return meta["content"].strip()

    t = soup.select_one("time[datetime]")
    if t and t.has_attr("datetime"):
        return t["datetime"].strip()

    t2 = soup.select_one("time")
    if t2 and t2.get_text(strip=True):
        return t2.get_text(strip=True)

    return None


def _parse_claim_text(soup: BeautifulSoup):
    """
    Extracts the claim text from the article.
    Based on the provided HTML, it's in a <span class="value"> inside a div with class "claim-review-block".
    """
    claim_block = soup.select_one("div.claim-review-block")
    if not claim_block:
        return None

    claim_value_div = claim_block.select_one("div.claim-value span.value")
    if claim_value_div:
        claim_text = claim_value_div.get_text(strip=True)
        return claim_text

    value_span = claim_block.select_one("span.value")
    if value_span:
        return value_span.get_text(strip=True)

    return None


def _parse_verdict(soup: BeautifulSoup):
    """
    Extracts the verdict from the article.
    Based on the provided HTML, it's in a <span class="value"> inside a div with class "claim-value" that has a heading "Fact Check:".
    """
    # Look for a div with class "claim-value" that contains a span with text "Fact Check:"
    fact_check_div = soup.select_one("div.claim-value span.heading.font-weight-bold:contains('Fact Check:')")
    if not fact_check_div:
        return "Unverified"
    
    # Find the next sibling span with class "value"
    value_span = fact_check_div.find_next_sibling()
    if value_span and isinstance(value_span, bs4.element.Tag) and 'value' in value_span.get('class', []):
        verdict_text = value_span.get_text(strip=True)
        return verdict_text.upper()  # Standardize to uppercase
    
    return "Unverified"


def _parse_originator(soup: BeautifulSoup):
    """
    Extracts the originator of the claim from the article.
    Based on the provided HTML, it's in a <span class="value"> after a label like "Claimed By".
    """
    claim_block = soup.select_one("div.claim-review-block")
    if claim_block:
        for elem in claim_block.descendants:
            if isinstance(elem, bs4.element.Tag) and 'claimed by' in elem.get_text(strip=True).lower():
                next_sibling = elem.find_next_sibling()
                if next_sibling and isinstance(next_sibling, bs4.element.Tag) and next_sibling.name == 'span' and 'value' in next_sibling.get('class', []):
                    return next_sibling.get_text(strip=True)

                parent = elem.parent
                if parent:
                    value_span = parent.select_one("span.value")
                    if value_span:
                        return value_span.get_text(strip=True)
                break

    # Fallback if specific parsing fails
    for strong_tag in soup.find_all('strong'):
        if 'claimed by' in strong_tag.get_text(strip=True).lower():
            next_elem = strong_tag.find_next_sibling()
            while next_elem:
                if isinstance(next_elem, bs4.element.Tag) and next_elem.name == 'span' and 'value' in next_elem.get('class', []):
                    return next_elem.get_text(strip=True)
                next_elem = next_elem.find_next_sibling()
            parent = strong_tag.parent
            if parent:
                value_span = parent.select_one("span.value")
                if value_span:
                    return value_span.get_text(strip=True)
            break

    return "Not Specified"


def _parse_full_article_text(soup: BeautifulSoup):
    """
    Extracts the full article text from the article.
    Based on the provided HTML, it's likely in a div with class "entry-content" or similar.
    """
    content_selectors = [
        "div.entry-content",
        "div.details-story-wrapper",
        "div.story-content",
        "div.article-body",
        "div.content"
    ]

    full_text_parts = []
    content_found = False

    for selector in content_selectors:
        content_div = soup.select_one(selector)
        if content_div:
            paragraphs = content_div.select("p")
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    full_text_parts.append(text)
            if full_text_parts:
                content_found = True
                break

    if not content_found:
        logger.warning("No standard article content area found, falling back to body text.")
        body = soup.select_one("body")
        if body:
            text = body.get_text(separator=' ', strip=True)
            if text:
                full_text_parts = [text[:5000]] # Limit to first 5000 chars as example
                logger.info("Used body text fallback (truncated).")
            else:
                logger.warning("Fallback body text extraction also failed or was empty.")
        else:
            logger.error("No <body> tag found in the article HTML.")
            return ""

    return "\n".join(full_text_parts)


# --- Updated Article Scraping with NER ---
def scrape_article(url: str):
    """Scrapes article details and extracts entities."""
    s = _soup(url)
    if not s:
        return None

    claim = _parse_claim_text(s)
    verdict = _parse_verdict(s)
    date_iso = _parse_iso_date(s)
    originator = _parse_originator(s)
    full_text = _parse_full_article_text(s)

    # Extract entities using SpaCy with deduplication
    entities_data = []
    seen_entities_for_article = set()
    if nlp and full_text:
        try:
            doc = nlp(full_text)
            for ent in doc.ents:
                spacy_to_custom_kind = {
                    "PERSON": "person",
                    "ORG": "org",
                    "GPE": "place",
                }
                kind = spacy_to_custom_kind.get(ent.label_, "topic")
                name = ent.text.strip()
                lang = "en"

                entity_key = (name.lower(), kind.lower(), lang.lower())
                if entity_key not in seen_entities_for_article:
                    seen_entities_for_article.add(entity_key)
                    entities_data.append({
                        "name": name,
                        "kind": kind,
                        "lang": lang
                    })
        except Exception as e:
            logger.warning(f"Error extracting entities for article {url}: {e}")

    return {
        "claim": claim,
        "verdict": verdict,
        "source_url": url,
        "date_iso": date_iso,
        "originator": originator,
        "entities_data": entities_data,
        "full_article_text": full_text
    }

# --- Scraper Run Management ---
def get_oldest_claim_date(scraper_name: str) -> datetime | None:
    """Fetches the oldest published_date from claims for this scraper."""
    db_session = Session()
    try:
        # IMPORTANT: Query for BoomLive's domain
        oldest_date = db_session.query(ClaimModel.published_date).filter(
            ClaimModel.source.has(Source.domain == 'boomlive.in')
        ).order_by(ClaimModel.published_date.asc()).first()

        if oldest_date and oldest_date[0]:
            return oldest_date[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching oldest claim date for {scraper_name}: {e}")
        return None
    finally:
        db_session.close()

def update_scraper_run(scraper_name: str, status: str, total_fetched: int, total_inserted: int):
    """Updates or creates a record in scraper_runs table."""
    db_session = Session()
    try:
        new_run = ScraperRuns(
            scraper_name=scraper_name,
            status=status,
            total_fetched=total_fetched,
            total_inserted=total_inserted
        )
        db_session.add(new_run)
        db_session.commit()
        logger.info(f"Scraper run record updated: {scraper_name}, Status: {status}, Fetched: {total_fetched}, Inserted: {total_inserted}")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to update scraper run record: {e}")
    finally:
        db_session.close()

# --- Main Scraping Logic ---
def scrape_boomlive(start_page: int = 1, max_pages: int | None = None):
    """Main scraping function with deduplication, NER, and scraper run tracking."""
    page = start_page
    total_fetched = 0
    total_inserted = 0
    seen_urls = set()
    stop_scraping = False
    # Initialize links to prevent UnboundLocalError
    links = []

    # --- Get the oldest claim date processed by this scraper ---
    oldest_claim_date = get_oldest_claim_date(SCRAPER_NAME)
    if oldest_claim_date:
        logger.info(f"Oldest claim date found: {oldest_claim_date}")
    else:
        logger.info("No previous claims found. Will scrape all available articles.")

    try:
        while True:
            if max_pages is not None and page >= start_page + max_pages:
                logger.info(f"[DONE] Reached max_pages at page {page}.")
                break
            if stop_scraping:
                logger.info("[STOP] Stop scraping condition met (article older than oldest known claim).")
                break

            archive_url = BASE_ARCHIVE.format(page)
            logger.info(f"\n=== Scraping BoomLive archive page {page}: {archive_url}")
            soup = _soup(archive_url)
            if not soup:
                logger.error("[STOP] Could not load archive page.")
                break

            # links is now guaranteed to be assigned in this path
            links = _extract_archive_links(soup)
            if not links:
                logger.info("[STOP] No article links found on this page. Assuming end of archive.")
                break

            logger.info(f"Found {len(links)} article links.")

            for idx, url in enumerate(links, start=1):
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                total_fetched += 1

                logger.info(f"  [{idx:02d}/{len(links)}] Article → {url}")

                data = scrape_article(url)
                time.sleep(SLEEP_BETWEEN_REQUESTS)

                if not data:
                    logger.warning("    [SKIP] Failed to scrape article.")
                    continue

                claim = data["claim"]
                verdict = data["verdict"]
                source_url = data["source_url"]
                date_iso = data["date_iso"]
                originator = data["originator"]
                entities_data = data["entities_data"]

                if not claim:
                    logger.warning("    [SKIP] No claim found.")
                    continue

                # --- Check if article is older than the oldest known claim ---
                article_datetime = None
                if date_iso:
                    try:
                        article_datetime = datetime.fromisoformat(date_iso.rstrip('Z'))
                    except ValueError:
                        logger.warning(f"    [WARN] Could not parse article datetime '{date_iso}'. Proceeding.")

                # --- Stop Condition Logic ---
                if oldest_claim_date and article_datetime and article_datetime <= oldest_claim_date:
                    logger.info(f"    [STOP] Article date ({article_datetime}) is older than/equal to oldest known claim ({oldest_claim_date}). Stopping scraper.")
                    stop_scraping = True
                    break

                # --- Insert into Database ---
                try:
                    if insert_claim_with_vector_v2(
                        text=claim,
                        verdict=verdict,
                        source_url=source_url,
                        short_points=None,
                        date=date_iso,
                        entities_data=entities_data,
                        fact_checker_platform='fact_checker',
                        fact_checker_handle='boomlive',
                        fact_checker_display_name='BoomLive',
                        raw_analysis_json=None
                    ):
                        total_inserted += 1
                        logger.info(f"    [OK] Inserted → verdict='{verdict}' date='{date_iso}' Entities: {len(entities_data)}")
                    else:
                        logger.info(f"    [SKIP] Skipped insert for {source_url} (duplicate, near-duplicate, or failure).")

                except Exception as e:
                    logger.error(f"    [ERR] Insertion failed for {source_url}: {e}", exc_info=True)

            page += 1

    finally:
        # --- Update scraper run record ---
        if page == start_page and not links:
            final_status = "failed"
        elif stop_scraping:
            final_status = "partial"
        else:
            final_status = "success"

        update_scraper_run(SCRAPER_NAME, final_status, total_fetched, total_inserted)
        logger.info(f"\n[SUMMARY] Fetched {total_fetched} articles, Inserted {total_inserted} articles.")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        start_page = int(sys.argv[1])
        max_pages = int(sys.argv[2]) if sys.argv[2].lower() != 'none' else None
    elif len(sys.argv) > 1:
        start_page = int(sys.argv[1])
        max_pages = 1
    else:
        start_page = 1
        max_pages = 1

    logger.info(f"Starting BoomLive scraper: start_page={start_page}, max_pages={max_pages}")
    scrape_boomlive(start_page=2, max_pages=1)
