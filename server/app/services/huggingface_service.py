# huggingface_service.py
import asyncio
import json
from huggingface_hub import InferenceClient
from app.config import HF_API_KEY

HF_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

client = InferenceClient(
    token=HF_API_KEY
)

async def query_llm(prompt: str) -> str:
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=HF_MODEL,
                max_tokens=400,
                temperature=0.2
            )
        )
        # Extract the response content
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Query Error: {str(e)}")
        return "Unable to process request at this time"