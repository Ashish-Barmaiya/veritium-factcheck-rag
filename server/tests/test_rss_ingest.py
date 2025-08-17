from unittest.mock import patch
from app.ingestion.rss_ingest import ingest_rss

@patch("ingestion.rss_ingest.insert_claim")
@patch("ingestion.rss_ingest.feedparser.parse")
def test_ingest(mock_parse, mock_insert):
    # Mock a fake RSS feed entry
    mock_parse.return_value.entries = [
        {"title":"Test Title","summary":"Test summary","link":"http://url","published":"2025-08-13"}
    ]
    ingest_rss()
    assert mock_insert.called, "insert_claim was not called"
