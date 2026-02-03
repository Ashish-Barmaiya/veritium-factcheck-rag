# Architecture

This document describes the system architecture of Veritium, an AI-powered fact-checking platform using Retrieval-Augmented Generation (RAG).

## System Overview

```mermaid
flowchart TB
    subgraph Client["Next.js Client"]
        UI["Fact-Check UI"]
        API_ROUTE["/api/factcheck"]
    end
    
    subgraph Server["FastAPI Server"]
        MAIN["main.py<br/>Endpoints"]
        EMB["Embedding Service<br/>all-MiniLM-L6-v2"]
        DB_SVC["DB Service"]
        HF_SVC["HuggingFace Service<br/>Mixtral-8x7B"]
        PARSE["LLM Response Parser"]
    end
    
    subgraph Storage["Data Layer"]
        QDRANT["Qdrant Cloud<br/>Vector Store"]
        PG["PostgreSQL<br/>Relational DB"]
    end
    
    subgraph Ingestion["Data Ingestion"]
        SCRAPERS["Scrapers<br/>Snopes, PolitiFact, etc."]
        NER["SpaCy NER"]
        DEDUP["SimHash Dedup"]
        OLLAMA["Ollama LLM"]
    end
    
    UI --> API_ROUTE --> MAIN
    MAIN --> EMB --> DB_SVC --> QDRANT
    DB_SVC --> PG
    MAIN --> HF_SVC --> PARSE
    
    SCRAPERS --> DEDUP --> NER --> OLLAMA --> DB_SVC
```

## RAG Pipeline

The fact-checking flow follows the standard RAG pattern:

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant Embeddings
    participant Qdrant
    participant LLM
    
    User->>FastAPI: POST /factcheck {claim}
    FastAPI->>Embeddings: get_embedding(claim)
    Embeddings-->>FastAPI: vector[384]
    FastAPI->>Qdrant: search(vector, top_k=1)
    Qdrant-->>FastAPI: Evidence + Metadata
    FastAPI->>LLM: prompt(claim + evidence)
    LLM-->>FastAPI: {verdict, explanation, sources}
    FastAPI-->>User: Fact-check result
```

### 1. Embedding Generation
- Model: `all-MiniLM-L6-v2` from Sentence Transformers
- Output: 384-dimensional vectors
- Optimized for semantic similarity

### 2. Vector Search
- Qdrant Cloud with COSINE distance
- Returns top-K most similar fact-checked claims
- Payload includes: `text`, `verdict`, `source_url`, `date`, `short_points`

### 3. LLM Verdict Generation
- Model: `mistralai/Mixtral-8x7B-Instruct-v0.1`
- HuggingFace Inference API
- Structured JSON output with verdict, explanation, sources

## Database Schema

```mermaid
erDiagram
    ClaimModel ||--o{ ClaimEntity : has
    ClaimModel ||--o{ ClaimEvent : has
    ClaimModel ||--o{ ClaimVariant : has
    ClaimModel }o--|| Source : belongs_to
    ClaimModel }o--|| Actor : fact_checked_by
    
    Source ||--o{ Actor : hosts
    Source ||--o{ ClaimEvent : from
    
    Actor ||--o{ ClaimEvent : performs
    Actor ||--o{ ActorMetricsDaily : has
    
    Entity ||--o{ ClaimEntity : linked
    
    VariantCluster ||--o{ ClaimVariant : contains
    VariantCluster ||--o{ EventVariant : contains
    
    ClaimModel {
        int id PK
        text claim_text
        string verdict
        string source_url UK
        date published_date
        string simhash
        text short_points
        text raw_analysis_json
    }
    
    Source {
        int id PK
        citext domain
        text kind
        text name
        char country_code
    }
    
    Actor {
        int id PK
        text platform
        citext handle
        text display_name
    }
    
    Entity {
        int id PK
        citext name
        text kind
        text lang
    }
```

### Core Models

| Model | Purpose |
|-------|---------|
| `ClaimModel` | Fact-checked claims with verdicts and metadata |
| `Source` | Origin domains (fact_checker, news, social, etc.) |
| `Actor` | Users/organizations that share or check claims |
| `Entity` | Named entities extracted via NER (person, org, place) |
| `ClaimEvent` | Claim lifecycle events (said, shared, debunked) |
| `VariantCluster` | Groups of semantically similar claims |
| `ScraperRuns` | Ingestion job tracking |

## Ingestion Pipeline

```mermaid
flowchart LR
    subgraph Scrapers
        S1["Snopes v3"]
        S2["PolitiFact v2"]
        S3["BoomLive v1"]
        S4["AltNews"]
        S5["AFP"]
        S6["Factly v2"]
    end
    
    subgraph Processing
        FETCH["HTTP Fetch<br/>+ Retry Logic"]
        PARSE["HTML Parse<br/>BeautifulSoup"]
        SIMHASH["SimHash<br/>Dedup Check"]
        NER["SpaCy NER<br/>Entity Extraction"]
        LLM["Ollama<br/>Key Points Extraction"]
    end
    
    subgraph Storage
        PG_I["PostgreSQL"]
        QD_I["Qdrant"]
    end
    
    S1 & S2 & S3 & S4 & S5 & S6 --> FETCH --> PARSE --> SIMHASH
    SIMHASH -->|New Claim| NER --> LLM
    LLM --> PG_I & QD_I
    SIMHASH -->|Duplicate| X["Skip"]
```

### Deduplication Strategy

- **SimHash Fingerprinting**: 64-bit fingerprint per claim
- **Hamming Distance Threshold**: ≤ 2 bits = near-duplicate
- Applied before insertion to prevent redundant data

### Entity Extraction

SpaCy NER maps to custom entity kinds:
- `PERSON` → `person`
- `ORG` → `org`
- `GPE` → `place`
- Others → `topic`

## Component Diagram

```mermaid
graph TB
    subgraph Frontend["Client (Next.js 15)"]
        PAGE["page.js<br/>Main UI"]
        NAVBAR["Navbar.jsx"]
        CARD["Card.jsx"]
    end
    
    subgraph Backend["Server (FastAPI)"]
        subgraph Core
            MAIN_PY["main.py"]
            MODELS["models.py"]
            CONFIG["config.py"]
        end
        
        subgraph Services
            EMB_SVC["embedding_service.py"]
            DB_SVC_2["db_service.py"]
            HF_SVC_2["huggingface_service.py"]
            OLLAMA_SVC["ollama_service.py"]
        end
        
        subgraph Utils
            SIMHASH_U["compute_simhash.py"]
            PARSE_U["safe_parse_llm_response.py"]
        end
        
        subgraph Ingestion_2["Ingestion"]
            SNOPES["scrape_snopes_v3.py"]
            POLITIFACT["scrape_politifact_v2.py"]
            OTHERS["...other scrapers"]
        end
    end
    
    PAGE --> MAIN_PY
    MAIN_PY --> EMB_SVC & DB_SVC_2 & HF_SVC_2
    DB_SVC_2 --> SIMHASH_U
    HF_SVC_2 --> PARSE_U
    SNOPES & POLITIFACT & OTHERS --> DB_SVC_2 & OLLAMA_SVC
```

## Technology Decisions

| Decision | Rationale |
|----------|-----------|
| **Qdrant over Pinecone** | Self-hostable, gRPC support, rich filtering |
| **Mixtral over GPT-4** | Open weights, cost-effective, good instruction following |
| **SimHash over exact match** | Detects paraphrased duplicates efficiently |
| **SpaCy for NER** | Fast, local, no API costs for entity extraction |
| **Alembic migrations** | Versioned schema changes, rollback support |

## Scaling Considerations

1. **Vector Search**: Qdrant supports sharding and replication
2. **Database**: PostgreSQL connection pooling with pgBouncer
3. **Embeddings**: Batch encoding for ingestion pipelines
4. **Rate Limiting**: Scraper throttling to respect source sites
5. **Caching**: Redis for LLM response caching (future)
