# server/app/services/db_service.py

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid
from app.config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME

client = QdrantClient(QDRANT_URL, api_key=QDRANT_API_KEY)

# Create collection if not exists
def init_collection():
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

def insert_claim(text, verdict, source_url, date, embedding):
    """
    Insert a claim into Qdrant with its embedding.
    Embedding must be provided by the caller.
    """
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": text,
                    "verdict": verdict,
                    "source_url": source_url,
                    "date": date
                }
            )
        ]
    )

def search_claim(query_embedding, top_k=1):
    # query_embedding is already a list of floats
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k
    )
    return results

# Initialize collection on import
init_collection()
