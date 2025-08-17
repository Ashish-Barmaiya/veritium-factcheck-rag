from unittest.mock import patch
from app.services.db_service import insert_claim, search_claim

@patch("services.db_service.client")
def test_insert_claim(mock_client):
    insert_claim("Test claim", "True", "http://source", "2025-08-13")
    assert mock_client.upsert.called, "DB upsert was not called"

@patch("services.db_service.client")
def test_search_claim(mock_client):
    mock_client.search.return_value = [
        {"score": 0.9, "payload": {"text": "Test", "verdict": "True", "source_url": "url", "date": "today"}}
    ]
    results = search_claim("Test")
    assert results[0]["payload"]["text"] == "Test"
