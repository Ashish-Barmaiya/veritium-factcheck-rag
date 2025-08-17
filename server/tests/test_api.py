from app.main import app  # Fixed import
from app.services import db_service  # Only import necessary service
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)  # Use the imported app

def test_search_endpoint(monkeypatch):
    # Patch get_embedding where it's used in db_service
    monkeypatch.setattr(
        "app.services.db_service.get_embedding", 
        lambda x: [0.1] * 384
    )

    # Mock search_claim
    def fake_search_claim(query_embedding, top_k=5):
        class FakeResult:
            def __init__(self):
                self.score = 0.9
                self.payload = {
                    "text": "Test claim",
                    "verdict": "True",
                    "source_url": "http://example.com",
                    "date": "2025-08-13"
                }
        return [FakeResult()]

    monkeypatch.setattr(
        "app.services.db_service.search_claim", 
        fake_search_claim
    )

    res = client.post("/search", json={"text": "This is a test claim"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["text"] == "Test claim"