import re
import json

def safe_parse_llm_response(response_text: str):
    try:
        # Extract the first {...} JSON block
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    
    # fallback
    return {
        "verdict": "Unverified",
        "explanation": "Unable to parse LLM response",
        "sources": []
    }
