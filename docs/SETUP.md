# Development Setup Guide

This guide walks through setting up a complete development environment for Veritium.

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| PostgreSQL | 14+ | Relational database |
| Ollama | latest | Local LLM (optional) |

**External Services:**
- Qdrant Cloud account → [cloud.qdrant.io](https://cloud.qdrant.io)
- HuggingFace API token → [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

## Environment Variables

Create a `.env` file in the project root:

```env
# ===== Qdrant Vector Database =====
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_URL=https://your-cluster-id.cloud.qdrant.io:6333
COLLECTION_NAME=veritium-v1

# ===== HuggingFace LLM =====
HF_API_KEY=hf_your_api_key_here

# ===== PostgreSQL =====
PG_DB_URL=postgresql+psycopg2://postgres:password@localhost:5432/veritium

# ===== Scraper Configuration =====
SCRAPER_REQUEST_TIMEOUT=15
SCRAPER_MAX_RETRIES=3
SCRAPER_SLEEP_BETWEEN_RETRIES=0.35
```

## PostgreSQL Setup

### Option 1: Local Installation

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14

# Windows: Download from postgresql.org
```

### Option 2: Docker

```bash
docker run -d \
  --name veritium-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=veritium \
  -p 5432:5432 \
  postgres:14
```

### Create Database

```bash
psql -U postgres
```
```sql
CREATE DATABASE veritium;
\q
```

## Qdrant Setup

### Option 1: Qdrant Cloud (Recommended)

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a new cluster
3. Copy the API key and URL to `.env`

### Option 2: Local Qdrant

```bash
docker run -d \
  --name veritium-qdrant \
  -p 6333:6333 \
  qdrant/qdrant
```

Update `.env`:
```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local
```

## Server Setup

```bash
cd server

# Create virtual environment
python -m venv venv

# Activate (choose your OS)
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows CMD
.\venv\Scripts\Activate.ps1   # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Download SpaCy model for NER
python -m spacy download en_core_web_sm
```

### Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Check current migration
alembic current

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"
```

### Run the Server

```bash
# Development with auto-reload
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will be available at: `http://localhost:8000`

API docs at: `http://localhost:8000/docs`

## Client Setup

```bash
cd client

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
npm run start
```

Client will be available at: `http://localhost:3000`

## Ollama Setup (Optional)

For local LLM-based key point extraction during ingestion:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start server
ollama serve

# Pull a model
ollama pull llama3.2
```

## Testing

```bash
cd server

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Common Issues

### "Module not found" errors
```bash
# Ensure you're in the activated venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database connection refused
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check Docker container
docker ps | grep postgres
```

### Qdrant connection failed
- Verify `QDRANT_URL` includes the port (`:6333`)
- For cloud, check API key is valid
- For local, ensure Docker container is running

### SpaCy model missing
```bash
python -m spacy download en_core_web_sm
```

### HuggingFace rate limited
- The free tier has limits; consider upgrading for heavy usage
- Implement response caching in production

## Development Workflow

1. **Start services:**
   ```bash
   cd server && source venv/bin/activate && uvicorn app.main:app --reload
   ```
   ```bash
   cd client && npm run dev
   ```

2. **Make code changes**

3. **Test API:**
   ```bash
   curl http://localhost:8000/
   curl -X POST http://localhost:8000/factcheck \
     -H "Content-Type: application/json" \
     -d '{"claim": "test claim"}'
   ```

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

5. **Check logs** for errors in both terminal windows
