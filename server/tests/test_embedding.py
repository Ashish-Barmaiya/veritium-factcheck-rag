import pytest
from app.services.embedding_service import get_embedding

def test_embedding_shape():
    text = "Hello world"
    emb = get_embedding(text)
    assert isinstance(emb, list)
    assert len(emb) == 384  # embedding dimension of 'all-MiniLM-L6-v2'

def test_empty_text():
    import pytest
    with pytest.raises(ValueError):
        get_embedding("")
