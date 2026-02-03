# API Reference

This document details the REST API endpoints exposed by the Veritium FastAPI server.

## Base URL

```
http://localhost:8000
```

## Endpoints

### GET /

Health check endpoint.

**Response:**
```json
{
  "message": "Welcome to the Fact-Check API. Use /search to find claims."
}
```

---

### POST /search

Performs semantic search over the claim database to find the most similar fact-checked claims.

**Request Body:**
```json
{
  "text": "string (required) - The search query"
}
```

**Response:**
```json
[
  {
    "id": 123,
    "score": 0.92,
    "text": "Claim text from the database",
    "verdict": "False",
    "source_url": "https://www.snopes.com/...",
    "date": "2024-01-15T12:00:00Z"
  }
]
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Claim ID in the database |
| `score` | float | Cosine similarity score (0-1) |
| `text` | string | Original claim text |
| `verdict` | string | Fact-check verdict |
| `source_url` | string | URL of the fact-check article |
| `date` | string | Publication date (ISO 8601) |

**Example:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"text": "vaccine microchip"}'
```

---

### POST /factcheck

Full RAG fact-checking pipeline: embeds the claim, retrieves evidence, and generates an LLM verdict.

**Request Body:**
```json
{
  "claim": "string (required) - The claim to verify"
}
```

**Response:**
```json
{
  "claim": "COVID-19 vaccines contain microchips",
  "evidence": "- No, COVID-19 vaccines do not contain microchips (Source: snopes.com, Date: 2021-03-15, verdict: False) | Points: Vaccines contain mRNA, lipids, and salts only",
  "llm_response": {
    "verdict": "False",
    "explanation": "There is no credible evidence that COVID-19 vaccines contain any tracking devices or microchips. The ingredients of approved vaccines are well-documented and publicly available.",
    "sources": ["https://www.snopes.com/fact-check/covid-vaccine-microchip/"]
  }
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `claim` | string | Original claim from request |
| `evidence` | string | Retrieved evidence from vector DB |
| `llm_response.verdict` | string | AI-generated verdict |
| `llm_response.explanation` | string | Reasoning for the verdict |
| `llm_response.sources` | array | Source URLs from evidence |

**Possible Verdicts:**
- `True`, `Mostly True`, `Half True`, `Barely True`
- `False`, `Mostly False`
- `Misleading`, `Satire`, `Incorrect Attribution`, `Miscaptioned`
- `Unverified` (fallback when parsing fails)

**Example:**
```bash
curl -X POST http://localhost:8000/factcheck \
  -H "Content-Type: application/json" \
  -d '{"claim": "The earth is flat"}'
```

---

## Request/Response Models

### SearchRequest
```python
class SearchRequest(BaseModel):
    text: str  # Query text for semantic search
```

### FactCheckRequest
```python
class FactCheckRequest(BaseModel):
    claim: str  # Claim to fact-check
```

---

## Error Handling

The API uses standard HTTP status codes:

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad Request (invalid input) |
| `422` | Validation Error (missing fields) |
| `500` | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message describing the issue"
}
```

---

## Rate Limits

Currently no rate limiting is implemented. For production use, consider adding rate limiting middleware.

---

## CORS

CORS is not configured by default. Add appropriate middleware for cross-origin requests from the client.
