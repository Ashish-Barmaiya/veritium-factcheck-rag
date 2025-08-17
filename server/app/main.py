from fastapi import FastAPI
from pydantic import BaseModel
from app.services.embedding_service import get_embedding
from app.services.db_service import search_claim
from app.services.huggingface_service import query_llm

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
    for r in results
])

    prompt = f"""
    Claim: {request.claim}

    Evidence:
    {evidence_text}

    Task: Based on the evidence above, determine if the claim is True, False, or Misleading.
    Respond strictly in valid JSON with:
    {{
      "verdict": "True" | "False" | "Misleading",
      "explanation": "<brief reasoning>",
      "sources": ["<source_url1>", "<source_url2>", ...]
    }}
    """

    llm_response = await query_llm(prompt)

    return {
        # TODO: Send title of the top matched article 
        "claim": request.claim,
        "evidence": evidence_text,
        "llm_response": llm_response
    }