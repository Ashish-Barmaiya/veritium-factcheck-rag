# Data Ingestion Guide

This document describes how to run, configure, and extend the data ingestion pipeline.

## Overview

Veritium ingests fact-checked claims from multiple sources using web scrapers. Each scraper:
1. Fetches article URLs from archive pages
2. Parses claim, verdict, and metadata
3. Extracts entities using SpaCy NER
4. Generates key points using Ollama LLM
5. Inserts into PostgreSQL and Qdrant (with deduplication)

## Supported Sources

| Source | Scraper File | Status | Notes |
|--------|--------------|--------|-------|
| **Snopes** | `scrape_snopes_v3.py` | ✅ Production | Full NER, LLM extraction, incremental |
| **PolitiFact** | `scrape_politifact_v2.py` | ✅ Production | Enhanced parsing |
| **BoomLive** | `scrape_boomlive_v1.py` | ✅ Production | Indian fact-checker |
| **AltNews** | `scrape_altnews.py` | ⚠️ Basic | Needs v2 upgrade |
| **AFP** | `scrape_afp.py` | ⚠️ Basic | Needs v2 upgrade |
| **Factly** | `scrape_factly_v2.py` | ✅ Production | Indian fact-checker |
| **FactCheck.org** | `scrape_factcheck_org.py` | ⚠️ Basic | — |

## Running Scrapers

### Prerequisites

```bash
# Activate virtual environment
cd server
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install SpaCy model (required for NER)
python -m spacy download en_core_web_sm

# Ensure Ollama is running (for LLM extraction)
ollama serve
```

### Run a Single Scraper

```bash
# Snopes (recommended starting point)
python -m app.ingestion.scrape_snopes_v3

# PolitiFact
python -m app.ingestion.scrape_politifact_v2

# BoomLive
python -m app.ingestion.scrape_boomlive_v1
```

### Configure Scraper Parameters

In `scrape_snopes_v3.py`:
```python
if __name__ == "__main__":
    scrape_snopes_v3(
        start_page=1,    # Start from page 1 of archive
        max_pages=10     # Process 10 pages (None = until end)
    )
```

## Scraper Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Scraper Flow                              │
├─────────────────────────────────────────────────────────────────┤
│  1. Fetch Archive Page                                          │
│     └─> Extract article URLs                                    │
│                                                                 │
│  2. For each article URL:                                       │
│     ├─> Fetch article page                                      │
│     ├─> Parse: claim, verdict, date                             │
│     ├─> Extract full article text                               │
│     ├─> SpaCy NER: extract entities                             │
│     ├─> Ollama: extract key evidence points                     │
│     └─> Insert via db_service                                   │
│                                                                 │
│  3. Deduplication:                                              │
│     ├─> SimHash check against existing claims                   │
│     └─> Skip if Hamming distance ≤ 2                            │
│                                                                 │
│  4. Storage:                                                    │
│     ├─> PostgreSQL: full metadata + entities                    │
│     └─> Qdrant: embedding + payload                             │
└─────────────────────────────────────────────────────────────────┘
```

## Deduplication Strategy

### SimHash Algorithm

SimHash creates a 64-bit fingerprint for each claim text:

```python
from simhash import Simhash

SIMHASH_FINGERPRINT_SIZE = 64
SIMHASH_THRESHOLD = 2  # Max Hamming distance for "duplicate"

def compute_simhash(text: str) -> str:
    return str(Simhash(text, f=SIMHASH_FINGERPRINT_SIZE).value)
```

### Deduplication Check

Before inserting a new claim:
1. Compute SimHash of the new claim
2. Compare against all existing claim hashes
3. If Hamming distance ≤ 2: skip (near-duplicate)
4. Otherwise: proceed with insertion

## Entity Extraction

SpaCy NER extracts named entities and maps to custom types:

| SpaCy Label | Veritium Kind |
|-------------|---------------|
| `PERSON` | `person` |
| `ORG` | `org` |
| `GPE` | `place` |
| Others | `topic` |

Example output:
```python
entities_data = [
    {"name": "Joe Biden", "kind": "person", "lang": "en"},
    {"name": "CDC", "kind": "org", "lang": "en"},
    {"name": "United States", "kind": "place", "lang": "en"}
]
```

## LLM Key Point Extraction

Uses Ollama (local LLM) to extract structured information:

```python
from app.services.ollama_service import extract_structured_info

result = extract_structured_info(full_article_text)
# Returns:
# {
#   "key_evidence": ["Point 1", "Point 2", ...],
#   "summary": "...",
#   ...
# }
```

## Configuration

Environment variables in `.env`:

```env
# Scraper behavior
SCRAPER_REQUEST_TIMEOUT=15      # Seconds to wait for HTTP response
SCRAPER_MAX_RETRIES=3           # Number of retry attempts
SCRAPER_SLEEP_BETWEEN_RETRIES=0.35  # Seconds between requests
```

## Adding a New Scraper

1. Create `server/app/ingestion/scrape_[source]_v1.py`

2. Implement required functions:
```python
def _fetch(url):
    """HTTP GET with retry logic."""
    
def _soup(url):
    """Return BeautifulSoup of URL."""
    
def _extract_archive_links(soup):
    """Extract article URLs from archive page."""
    
def scrape_article(url):
    """Parse single article, return dict with:
    - claim, verdict, source_url, date_iso
    - entities_data, full_article_text
    """

def scrape_[source](start_page, max_pages):
    """Main loop over archive pages."""
```

3. Call the insertion function:
```python
from app.services.db_service import insert_claim_with_vector_v2

insert_claim_with_vector_v2(
    text=claim,
    verdict=verdict,
    source_url=url,
    short_points=key_points,
    date=date_iso,
    entities_data=entities,
    fact_checker_platform='fact_checker',
    fact_checker_handle='source_name',
    fact_checker_display_name='Source Name'
)
```

## Scraper Run Tracking

Each scraper run is logged in the `scraper_runs` table:

| Field | Description |
|-------|-------------|
| `scraper_name` | Identifier (e.g., `snopes_fact_checks`) |
| `last_run` | Timestamp of run |
| `status` | `success`, `partial`, or `failed` |
| `total_fetched` | Articles visited |
| `total_inserted` | New claims inserted |

Query recent runs:
```sql
SELECT * FROM scraper_runs 
ORDER BY last_run DESC 
LIMIT 10;
```

## Best Practices

1. **Respect rate limits**: Configure appropriate sleep intervals
2. **Incremental scraping**: Use date-based stop conditions
3. **Error handling**: Log failures, don't crash on single article
4. **Testing**: Test with `max_pages=1` before full runs
5. **Monitoring**: Check `scraper_runs` table after ingestion
