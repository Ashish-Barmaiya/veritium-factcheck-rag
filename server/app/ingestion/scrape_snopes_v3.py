# server/app/ingestion/scrape_snopes_v3.py

import sys
import time
import logging
import requests
import asyncio
import json  # Import json for serialization
from bs4 import BeautifulSoup
from datetime import datetime
import spacy  # For NER

# Import your updated functions and models
from app.services.db_service import insert_claim_with_vector_v2, Session
from app.models import ScraperRuns, ClaimModel, Source # Import ScraperRuns model
from app.services.ollama_service import extract_structured_info # Import local LLM function

# Import config (assuming these are defined)
# Make sure these are correctly imported from your config
from app.config import REQUEST_TIMEOUT, SLEEP_BETWEEN_REQUESTS, MAX_RETRIES 

# --- Configuration ---
BASE_ARCHIVE = "https://www.snopes.com/fact-check/?pagenum={}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )
}
SCRAPER_NAME = "snopes_fact_checks"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Spacy NLP Model (Load once) ---
try:
    nlp = spacy.load("en_core_web_sm")  # Or a larger model if needed
    logger.info("Spacy NLP model loaded successfully.")
except OSError:
    logger.error("Spacy model 'en_core_web_sm' not found. Please install it using `python -m spacy download en_core_web_sm`")
    nlp = None  # Disable NER if model not found


# --- Scraper Helper Functions (Copied/Adapted from v2) ---
def _fetch(url):
    """GET with basic retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            # 4xx other than 429: likely permanent for this URL
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                logger.warning(f"{resp.status_code} for {url}")
                return resp
            # 5xx or 429: retry
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

# --- Updated Article Scraping with NER ---
def scrape_article(url: str):
    """Scrapes article details and extracts entities."""
    s = _soup(url)
    if not s:
        return None

    claim = _parse_claim_text(s)
    verdict = _parse_verdict(s)
    date_iso = _parse_iso_date(s)  # This is the full ISO string

    # Extract full article
    article_content = s.select_one("#article-content")
    if not article_content:
        logger.warning(f"No article content found for {url}")
        full_text = ""
    else:
        # Find all paragraph (<p>) and blockquote elements within the article
        paragraphs = article_content.select("p[dir='ltr'], blockquote")
        full_text_parts = []
        
        for p in paragraphs:
            # Get the text and strip whitespace
            text = p.get_text(strip=True)
            if text:
                full_text_parts.append(text)
        
        # Join all parts with a newline
        full_text = "\n".join(full_text_parts)

    entities_data = []
    seen_entities_for_article = set() # Deduplication entities within articl
    if nlp and full_text:
        try:
            doc = nlp(full_text)
            for ent in doc.ents:
                # Filter or map Spacy labels to your entity kinds if needed
                spacy_to_custom_kind = {
                    "PERSON": "person",
                    "ORG": "org",
                    "GPE": "place",  # Geopolitical entity
                    # Add more mappings as needed
                }
                kind = spacy_to_custom_kind.get(ent.label_, "topic")  # Default to topic
                name = ent.text.strip()
                lang = "en"
                # Create a unique key for the entity within this article
                entity_key = (name.lower(), kind.lower(), lang.lower())
                # Check if we've already added this entity for this article
                if entity_key not in seen_entities_for_article:
                    seen_entities_for_article.add(entity_key) # Mark as seen
                    entities_data.append({
                        "name": name,
                        "kind": kind,
                        "lang": lang
                    })
        except Exception as e:
             logger.warning(f"Error extracting entities for article {url}: {e}") # Log URL for context

    return {
        "claim": claim,
        "verdict": verdict,
        "source_url": url,
        "date_iso": date_iso,  # Full ISO string
        "entities_data": entities_data,
        "full_article_text": full_text # Return full text for LLM processing
    }

# --- Scraper Run Management ---
def get_oldest_claim_date(scraper_name: str) -> datetime | None:
    """Fetches the oldest published_date from claims for this scraper."""
    db_session = Session()
    try:
        # Query the oldest published_date for claims linked to this scraper
        # We assume the source_id or fact_checker_id links back to the scraper context
        # For simplicity, we'll assume all Snopes claims have a source with domain 'snopes.com'
        # Adjust this logic based on how you track scraper context in your DB
        oldest_date = db_session.query(ClaimModel.published_date).filter(
            ClaimModel.source.has(Source.domain == 'snopes.com')  # Example filter
        ).order_by(ClaimModel.published_date.asc()).first()
        
        if oldest_date and oldest_date[0]:  # Check if result exists and date is not None
            return oldest_date[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching oldest claim date for {scraper_name}: {e}")
        return None
    finally:
        db_session.close() # Ensure session is closed

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
def scrape_snopes_v3(start_page: int, max_pages: int | None = None):
    """Main scraping function with deduplication, NER, and scraper run tracking."""
    page = start_page
    total_fetched = 0
    total_inserted = 0
    seen_urls = set()
    stop_scraping = False

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
                break # Stop scraping if article is older than the oldest known claim

            archive_url = BASE_ARCHIVE.format(page)
            logger.info(f"\n=== Scraping Snopes archive page {page}: {archive_url}")
            soup = _soup(archive_url)
            if not soup:
                logger.error("[STOP] Could not load archive page.")
                break

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
                # Respectful with delay
                time.sleep(SLEEP_BETWEEN_REQUESTS) 

                if not data:
                    logger.warning("    [SKIP] Failed to scrape article.")
                    continue

                claim = data["claim"]
                verdict = data["verdict"]
                source_url = data["source_url"]
                date_iso = data["date_iso"]  # Full ISO string
                full_text = data.get("full_article_text", "") # Get the full text
                entities_data = data["entities_data"] # This is deduplicated within article

                if not claim:
                    logger.warning("    [SKIP] No claim (H1) found.")
                    continue

                # --- Check if article is older than the oldest known claim ---
                article_datetime = None
                if date_iso:
                    try:
                        # Parse the full ISO datetime string
                        # Handle potential 'Z' suffix
                        article_datetime = datetime.fromisoformat(date_iso.rstrip('Z'))
                    except ValueError:
                        logger.warning(f"    [WARN] Could not parse article datetime '{date_iso}'. Proceeding.")

                # --- Stop Condition Logic ---
                # Only stop if we have an oldest claim date AND the current article is older than or equal to it
                if oldest_claim_date and article_datetime and article_datetime <= oldest_claim_date:
                    logger.info(f"    [STOP] Article date ({article_datetime}) is older than/equal to oldest known claim ({oldest_claim_date}). Stopping scraper.")
                    stop_scraping = True
                    break # Break inner loop to move to next page or stop

                # --- LLM Processing for key points and structured data ---
                llm_extracted_content = {}
                short_points_list = None # Initialize short_points
                raw_analysis_json_str = None # Initialize raw_analysis_json string

                if full_text:
                    llm_extracted_content = extract_structured_info(full_text)
                    key_evidence_list = llm_extracted_content.get('key_evidence', [])
                    if isinstance(key_evidence_list, list):
                         short_points_list = key_evidence_list
                    else:
                         logger.warning(f"LLM 'key_evidence' is not a list: {key_evidence_list}")
                         short_points_list = []

                    # Serialize the entire LLM response dictionary
                    raw_analysis_json_str = json.dumps(llm_extracted_content) if llm_extracted_content else None

                    if not llm_extracted_content:
                        logger.warning(f"LLM extraction returned empty or failed for {source_url}")

                # --- Insert using the new function ---
                try:
                    # Call the updated insertion function with Snopes-specific details and LLM data
                    if insert_claim_with_vector_v2(
                        text=claim,
                        verdict=verdict,
                        source_url=source_url,
                        short_points=short_points_list, # Pass LLM-extracted key evidence
                        date=date_iso,  # Pass full ISO string
                        entities_data=entities_data, # Pass extracted entities from SpaCy
                        fact_checker_platform='fact_checker', # As defined in your Actor model CheckConstraint
                        fact_checker_handle='snopes', # Unique handle for Snopes
                        fact_checker_display_name='Snopes', # Display name
                        raw_analysis_json=raw_analysis_json_str # Pass serialized LLM JSON response
                    ):
                        total_inserted += 1
                        logger.info(f"    [OK] Inserted → verdict='{verdict}' date='{date_iso}' Entities: {len(entities_data)}, LLM Points: {len(short_points_list) if short_points_list else 0}")
                    else:
                         # Log message is handled inside insert_claim_with_vector_v2
                         # Could be duplicate, simhash match, or insertion failure
                        logger.info(f"    [SKIP] Skipped insert for {source_url} (duplicate, near-duplicate, or failure).")

                except Exception as e:
                    logger.error(f"    [ERR] Insertion failed for {source_url}: {e}", exc_info=True)

            # Small pause between archive pages (optional, already delayed between articles)
            # time.sleep(SLEEP_BETWEEN_REQUESTS) 
            page += 1

    finally:
        # --- Update scraper run record ---
        # Determine final status
        if stop_scraping:
            final_status = "partial" # Stopped due to reaching historical data
        elif page == start_page and not links: # If the very first page failed/empty
             final_status = "failed"
        else:
            final_status = "success" # Reached max_pages or natural end

        update_scraper_run(SCRAPER_NAME, final_status, total_fetched, total_inserted)
        logger.info(f"\n[SUMMARY] Fetched {total_fetched} articles, Inserted {total_inserted} articles.")


if __name__ == "__main__":
    # Set max_pages=None to run until the archive ends or stop condition is met.
    scrape_snopes_v3(start_page=3, max_pages=1) # Example: scrape page 4 only
