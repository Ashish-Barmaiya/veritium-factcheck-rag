# server/app/services/embedding_service.py

from sentence_transformers import SentenceTransformer

# Load model once at startup
# 'all-MiniLM-L6-v2' → dimension = 384
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str):
    """
    Generate a vector embedding for the given text using Sentence Transformers.
    Returns a Python list of floats (ready for Qdrant).
    """
    if not text or not text.strip():
        raise ValueError("Input text for embedding cannot be empty.")
    
    # Encode text to a numpy array, then convert to list for Qdrant
    embedding = model.encode(text, convert_to_numpy=True).tolist()
    return embedding
