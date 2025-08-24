from fastapi import FastAPI
from pydantic import BaseModel
from app.services.embedding_service import get_embedding
from app.services.db_service import search_claim
from app.services.huggingface_service import query_llm
from app.utils.safe_parse_llm_response import safe_parse_llm_response

app = FastAPI()

class SearchRequest(BaseModel):
    text: str
class FactCheckRequest(BaseModel):
    claim: str

@app.get("/")
def root():
    return {"message": "Welcome to the Fact-Check API. Use /search to find claims."}

@app.post("/search")
def search_claims(request: SearchRequest):
    embedding = get_embedding(request.text)
    results = search_claim(embedding, top_k=5)
    return [
        {
            "id": r.id,
            "score": r.score,
            "text": r.payload["text"],
            "verdict": r.payload["verdict"],
            "source_url": r.payload["source_url"],
            "date": r.payload["date"]
        }
        for r in results
    ]

@app.post("/factcheck")
async def factcheck_claim(request: FactCheckRequest):
    # Get embedding
    embedding = get_embedding(request.claim)

    # Retrieve top-K evidence
    results = search_claim(embedding, top_k=1)

    evidence_text = "\n\n".join([
    f"- {r.payload['text']} "
    f"(Source: {r.payload['source_url']}, Date: {r.payload['date']}, "
    f"verdict: {r.payload['verdict'].replace('About this rating', '').strip()})"
    f"{' | Points: ' + ', '.join(r.payload['short_points']) if r.payload.get('short_points') else ''}"
    for r in results
])

    prompt = f"""
    Claim: {request.claim}

    Evidence:
    {evidence_text}

    Task: Based on the evidence above, determine the verdict of the claim.
    Use the same verdict categories as provided in the dataset (e.g., True, False, Mostly True, Mostly False, Half True, Barely True, Satire, Incorrect Attribution, etc.).
    {{
      "verdict": "<exact verdict label>",
      "explanation": "<brief reasoning>",
      "sources": ["<source_url1>", "<source_url2>", ...]
    }}
    """

    raw_response = await query_llm(prompt)
    llm_response = safe_parse_llm_response(raw_response)
    if not llm_response:
        llm_response = {
            "verdict": "Unverified",
            "explanation": "Unable to parse LLM response",
            "sources": []
        }

    return { 
        "claim": request.claim,
        "evidence": evidence_text,
        "llm_response": llm_response
    }