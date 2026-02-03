# Veritium — AI Fact-Checking with RAG

A full-stack AI fact-checking platform that uses **Retrieval-Augmented Generation (RAG)** to verify claims in real-time. The system combines semantic search over a curated database of fact-checked claims with LLM-based verdict generation.

## Features

- **Semantic Claim Search** — Query a vector database of fact-checked claims using natural language
- **AI-Powered Verdicts** — LLM generates verdicts with explanations based on retrieved evidence
- **Multi-Source Ingestion** — Automated scrapers for Snopes, PolitiFact, BoomLive, AltNews, AFP, and Factly
- **Near-Duplicate Detection** — SimHash-based deduplication prevents redundant claims
- **Entity Extraction** — SpaCy NER identifies people, organizations, and places in articles
- **Modern Web UI** — Next.js 15 frontend with real-time fact-checking interface

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────────────────────────────────────────┐
│   Next.js UI    │────▶│                  FastAPI Server                     │
│   (React 19)    │     │                                                     │
└─────────────────┘     │  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  │
                        │  │  Embedding  │  │   Qdrant   │  │  HuggingFace │  │
                        │  │  Service    │──▶│  Vector DB │  │  LLM (Mixtral│  │
                        │  └─────────────┘  └────────────┘  └──────────────┘  │
                        │                                                     │
                        │  ┌─────────────────────────────────────────────┐    │
                        │  │              PostgreSQL + Alembic            │    │
                        │  │  (Claims, Sources, Actors, Entities, Events) │    │
                        │  └─────────────────────────────────────────────┘    │
                        └─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Data Ingestion Pipeline                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Snopes  │  │Politifact│  │BoomLive │  │ AltNews │  │  AFP    │  + more   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │
│       │            │            │            │            │                 │
│       ▼            ▼            ▼            ▼            ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  SimHash Dedup → SpaCy NER → Ollama LLM → DB + Qdrant       │           │
│  └─────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, React 19, TailwindCSS v4 |
| **Backend** | FastAPI, Python 3.13 |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`, 384 dims) |
| **Vector DB** | Qdrant Cloud |
| **LLM** | HuggingFace Inference API (Mixtral-8x7B-Instruct) |
| **Database** | PostgreSQL + SQLAlchemy ORM + Alembic migrations |
| **NLP** | SpaCy (NER), SimHash (deduplication) |
| **Scraping** | Requests, BeautifulSoup, Playwright |

## Project Structure

```
veritium-factcheck-rag/
├── client/                      # Next.js frontend
│   ├── src/
│   │   ├── app/                 # App router pages
│   │   │   ├── page.js          # Main fact-check UI
│   │   │   └── how-it-works/    # Info pages
│   │   └── components/          # React components
│   └── package.json
│
├── server/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py              # FastAPI app & endpoints
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── config.py            # Environment config
│   │   ├── db.py                # Database connection
│   │   ├── services/
│   │   │   ├── db_service.py       # Qdrant + PostgreSQL ops
│   │   │   ├── embedding_service.py # Text embeddings
│   │   │   ├── huggingface_service.py # LLM queries
│   │   │   └── ollama_service.py    # Local LLM (Ollama)
│   │   ├── ingestion/           # Web scrapers
│   │   │   ├── scrape_snopes_v3.py
│   │   │   ├── scrape_politifact_v2.py
│   │   │   ├── scrape_boomlive_v1.py
│   │   │   └── ...
│   │   └── utils/
│   │       ├── compute_simhash.py   # Deduplication
│   │       └── safe_parse_llm_response.py
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Test suite
│   ├── graph/                   # DB schema visualization
│   └── requirements.txt
│
├── .env                         # Environment variables
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Qdrant Cloud account (or local instance)
- HuggingFace API token

### 1. Clone and Configure

```bash
git clone https://github.com/your-username/veritium-factcheck-rag.git
cd veritium-factcheck-rag

# Create .env file with your credentials
cp .env.example .env
```

Required environment variables:
```env
# Qdrant Vector Database
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
COLLECTION_NAME=veritium-v1

# HuggingFace LLM
HF_API_KEY=hf_your_api_key

# PostgreSQL
PG_DB_URL=postgresql+psycopg2://user:pass@localhost:5432/veritium

# Scraper Settings
SCRAPER_REQUEST_TIMEOUT=15
SCRAPER_MAX_RETRIES=3
SCRAPER_SLEEP_BETWEEN_RETRIES=0.35
```

### 2. Set Up the Server

```bash
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download SpaCy model
python -m spacy download en_core_web_sm

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Set Up the Client

```bash
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/search` | Semantic search over claims |
| `POST` | `/factcheck` | Full RAG fact-checking pipeline |

### POST /factcheck

**Request:**
```json
{
  "claim": "COVID-19 vaccines contain microchips"
}
```

**Response:**
```json
{
  "claim": "COVID-19 vaccines contain microchips",
  "evidence": "- No, COVID-19 vaccines do not contain microchips (Source: snopes.com, ...)",
  "llm_response": {
    "verdict": "False",
    "explanation": "There is no evidence that COVID-19 vaccines contain any tracking devices...",
    "sources": ["https://www.snopes.com/..."]
  }
}
```

## Data Ingestion

The system includes scrapers for multiple fact-checking sources:

| Source | File | Status |
|--------|------|--------|
| Snopes | `scrape_snopes_v3.py` | ✅ Production |
| PolitiFact | `scrape_politifact_v2.py` | ✅ Production |
| BoomLive | `scrape_boomlive_v1.py` | ✅ Production |
| AltNews | `scrape_altnews.py` | ⚠️ Basic |
| AFP | `scrape_afp.py` | ⚠️ Basic |
| Factly | `scrape_factly_v2.py` | ✅ Production |

Run a scraper:
```bash
cd server
python -m app.ingestion.scrape_snopes_v3
```

## Database Schema

Key models in `server/app/models.py`:

- **ClaimModel** — Fact-checked claims with verdict, source, and simhash
- **Source** — Domains categorized by type (fact_checker, news, social, etc.)
- **Actor** — Users/organizations that share claims
- **Entity** — Named entities (people, orgs, places) extracted via NER
- **ClaimEvent** — Claim lifecycle events (said, shared, debunked)
- **VariantCluster** — Groups of semantically similar claims
- **ScraperRuns** — Ingestion job tracking

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design and data flow
- [API Reference](docs/API.md) — Detailed endpoint documentation
- [Ingestion Guide](docs/INGESTION.md) — Running and extending scrapers
- [Setup Guide](docs/SETUP.md) — Development environment setup

## Testing

```bash
cd server
pytest tests/ -v
```

## License

MIT © 2025
