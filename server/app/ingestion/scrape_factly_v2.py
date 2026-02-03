# server/app/ingestion/scrape_factly_v1.py

import sys
import time
import logging
import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urljoin

# Playwright imports
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# BeautifulSoup for parsing HTML content fetched by Playwright
from bs4 import BeautifulSoup
import bs4

# Spacy for NER
import spacy

# Import your database functions and models
from app.services.db_service import insert_claim_with_vector_v2, Session
from app.models import ScraperRuns, ClaimModel, Source
# Import config (ensure these are defined)
from app.config import REQUEST_TIMEOUT, SLEEP_BETWEEN_REQUESTS, MAX_RETRIES

# --- Configuration ---
# Corrected URL format string
BASE_ARCHIVE = "https://factly.in/category/english/page/{}/"
SCRAPER_NAME = "factly_fact_checks"

# Playwright specific settings
PLAYWRIGHT_TIMEOUT = REQUEST_TIMEOUT * 1000  # Convert seconds to milliseconds
PLAYWRIGHT_HEADLESS = True  # Set to False for debugging

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

# --- Helper Functions (Run in Async Playwright Context) ---

async def _fetch_page_content(page, url: str, retries: int = MAX_RETRIES) -> str | None:
    """Fetches page content using Playwright with retries."""
    for attempt in range(1, retries + 1):
        try:
            logger.debug(f"Attempting to fetch {url} (Attempt {attempt}/{retries})")
            await page.goto(url, wait_until='networkidle', timeout=PLAYWRIGHT_TIMEOUT)
            # Optional: Wait for specific content to load if needed
            # await page.wait_for_selector('h1.post-title', timeout=PLAYWRIGHT_TIMEOUT)
            content = await page.content()
            logger.debug(f"Successfully fetched content for {url}")
            return content
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout fetching {url} on attempt {attempt}/{retries}")
        except Exception as e:
            logger.warning(f"Error fetching {url} on attempt {attempt}/{retries}: {e}")

        if attempt < retries:
            backoff = 0.5 * attempt
            logger.info(f"Retrying {url} in {backoff:.1f}s...")
            await asyncio.sleep(backoff)

    logger.error(f"Failed to fetch {url} after {retries} attempts.")
    return None


def _parse_archive_page(html_content: str) -> list[str]:
    """Parses the archive page HTML to extract article links."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    # Target the <a> inside <h1 class="post-title">
    for a in soup.select("h1.post-title a[href]"):
        href = a.get("href", "").strip()
        if href:
            # Ensure absolute URL
            full_url = urljoin("https://factly.in", href) if href.startswith('/') else href
            links.add(full_url)
    return sorted(list(links))


def _parse_article_page(html_content: str, url: str) -> dict | None:
    """Parses the article page HTML to extract claim, verdict, date, etc."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if not soup.find('body'):
        logger.warning(f"Empty or invalid HTML content received for {url}")
        return None

    # --- Extract Claim ---
    claim = None
    blockquote = soup.select_one("blockquote.wp-block-quote")
    if blockquote:
        p_tag = blockquote.select_one("p")
        if p_tag:
            claim_parts = []
            for child in p_tag.children:
                if isinstance(child, bs4.element.NavigableString):
                    claim_parts.append(child.strip())
                elif isinstance(child, bs4.element.Tag) and child.name != 'strong':
                    if hasattr(child, 'get_text'):
                        claim_parts.append(child.get_text(strip=True))
            claim_text = " ".join(claim_parts).strip()
            if claim_text.startswith("Claim:"):
                claim_text = claim_text[6:].strip()
            claim = claim_text

    # --- Extract Verdict ---
    verdict = "Unverified"
    if blockquote:
        p_tags = blockquote.select("p")
        if len(p_tags) >= 2:
            second_p = p_tags[1]
            strong_tags = second_p.select("strong")
            if strong_tags:
                verdict_text = strong_tags[-1].get_text(strip=True)
                verdict = verdict_text.upper()

    # --- Extract Date ---
    date_iso = None
    time_elem = soup.select_one("time.value-title")
    if time_elem and time_elem.has_attr("datetime"):
        date_iso = time_elem["datetime"].strip()
    else:
        t = soup.select_one("time")
        if t and t.get_text(strip=True):
            date_iso = t.get_text(strip=True) # Fallback, might not be ISO

    # --- Extract Summary ---
    summary = None
    if blockquote:
        p_tags = blockquote.select("p")
        if len(p_tags) >= 2:
            second_p = p_tags[1]
            full_text = second_p.get_text(strip=True)
            # Remove the final verdict (e.g., "FALSE.") from the end
            cleaned_text = re.sub(r'\b\w+\.$', '', full_text).strip()
            summary = cleaned_text

    # --- Extract Full Article Text ---
    full_text = ""
    article_content = soup.select_one(".post-content-right")
    if article_content:
        paragraphs = article_content.select("p, blockquote")
        full_text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        full_text = "\n".join(full_text_parts)

    # --- Extract Entities ---
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
        "summary": summary,
        "entities_data": entities_data,
        "full_article_text": full_text
    }

# --- Scraper Run Management (Synchronous DB calls) ---

def get_oldest_claim_date(scraper_name: str) -> datetime | None:
    """Fetches the oldest published_date from claims for this scraper."""
    db_session = Session()
    try:
        oldest_date = db_session.query(ClaimModel.published_date).filter(
            ClaimModel.source.has(Source.domain == 'factly.in')
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

# --- Main Scraping Logic (Async) ---

async def scrape_factly_v1_async(start_page: int, max_pages: int | None = None):
    """Main asynchronous scraping function using Playwright."""
    total_fetched = 0
    total_inserted = 0
    seen_urls = set()
    stop_scraping = False

    oldest_claim_date = get_oldest_claim_date(SCRAPER_NAME)
    if oldest_claim_date:
        logger.info(f"Oldest claim date found: {oldest_claim_date}")
    else:
        logger.info("No previous claims found. Will scrape all available articles.")

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        # Create a new context (like a new browser profile)
        context = await browser.new_context()
        # Set a common user agent
        await context.set_extra_http_headers({
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        })
        # Create a new page
        page = await context.new_page()
        # Set default timeout for page actions
        page.set_default_timeout(PLAYWRIGHT_TIMEOUT)

        page_num = start_page
        try:
            while True:
                if max_pages is not None and page_num >= start_page + max_pages:
                    logger.info(f"[DONE] Reached max_pages at page {page_num}.")
                    break
                if stop_scraping:
                    logger.info("[STOP] Stop scraping condition met (article older than oldest known claim).")
                    break

                archive_url = BASE_ARCHIVE.format(page_num)
                logger.info(f"\n=== Scraping Factly archive page {page_num}: {archive_url}")

                html_content = await _fetch_page_content(page, archive_url)
                if not html_content:
                    logger.error("[STOP] Could not load archive page.")
                    break

                links = _parse_archive_page(html_content)
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

                    article_html = await _fetch_page_content(page, url)
                    # Respectful delay
                    await asyncio.sleep(SLEEP_BETWEEN_REQUESTS)

                    if not article_html:
                        logger.warning("    [SKIP] Failed to fetch article page.")
                        continue

                    data = _parse_article_page(article_html, url)
                    if not data:
                        logger.warning("    [SKIP] Failed to parse article content.")
                        continue

                    claim = data["claim"]
                    verdict = data["verdict"]
                    source_url = data["source_url"]
                    date_iso = data["date_iso"]
                    summary = data["summary"]
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

                    if oldest_claim_date and article_datetime and article_datetime <= oldest_claim_date:
                        logger.info(f"    [STOP] Article date ({article_datetime}) is older than/equal to oldest known claim ({oldest_claim_date}). Stopping scraper.")
                        stop_scraping = True
                        break # Break inner loop

                    # --- Insert into Database ---
                    try:
                        if insert_claim_with_vector_v2(
                            text=claim,
                            verdict=verdict,
                            source_url=source_url,
                            short_points=[summary] if summary else None,
                            date=date_iso,
                            entities_data=entities_data,
                            fact_checker_platform='fact_checker',
                            fact_checker_handle='factly',
                            fact_checker_display_name='Factly',
                            raw_analysis_json=None
                        ):
                            total_inserted += 1
                            logger.info(f"    [OK] Inserted → verdict='{verdict}' date='{date_iso}' Entities: {len(entities_data)}, Summary Length: {len(summary) if summary else 0}")
                        else:
                            logger.info(f"    [SKIP] Skipped insert for {source_url} (duplicate, near-duplicate, or failure).")
                    except Exception as e:
                        logger.error(f"    [ERR] Insertion failed for {source_url}: {e}", exc_info=True)

                page_num += 1

        finally:
            await browser.close()

    # --- Update scraper run record ---
    final_status = "partial" if stop_scraping else ("failed" if page_num == start_page and not links else "success")
    update_scraper_run(SCRAPER_NAME, final_status, total_fetched, total_inserted)
    logger.info(f"\n[SUMMARY] Fetched {total_fetched} articles, Inserted {total_inserted} articles.")


# --- Synchronous Wrapper to Run Async Function ---
def scrape_factly_v1(start_page: int, max_pages: int | None = None):
    """Synchronous wrapper to run the async scraper."""
    asyncio.run(scrape_factly_v1_async(start_page, max_pages))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        start_page = int(sys.argv[1])
        max_pages = int(sys.argv[2]) if sys.argv[2].lower() != 'none' else None
    elif len(sys.argv) > 1:
        start_page = int(sys.argv[1])
        max_pages = 1 # Default to 1 page if only start_page is given
    else:
        start_page = 1
        max_pages = 1 # Default to page 1 only

    logger.info(f"Starting Factly scraper: start_page={start_page}, max_pages={max_pages}")
    scrape_factly_v1(start_page=start_page, max_pages=max_pages)
