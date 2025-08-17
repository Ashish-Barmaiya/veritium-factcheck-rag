# server/app/ingestion/rss_ingest.py

import feedparser
import re
from datetime import datetime
from app.services.embedding_service import get_embedding
from app.services.db_service import insert_claim

SOURCES = [
    {"name": "Snopes", "url": "https://www.snopes.com/feed/"},
    {"name": "BoomLive", "url": "https://www.boomlive.in/rss.xml"},
    {"name": "PolitiFact", "url": "https://www.politifact.com/rss/factchecks/"},
    {"name": "FactCheck.org", "url": "https://www.factcheck.org/feed/"},
    {"name": "AFP Fact Check", "url": "https://factcheck.afp.com/rss"},
    {"name": "AltNews", "url": "https://www.altnews.in/feed/"}
]

VERDICT_KEYWORDS = {
    "false": "False",
    "true": "True",
    "misleading": "Misleading",
    "satire": "Satire",
    "unproven": "Unproven",
    "outdated": "Outdated"
}

def clean_html(raw_html):
    clean_re = re.compile('<.*?>')
    return re.sub(clean_re, '', raw_html)

def extract_verdict(title, summary):
    text = (title + " " + summary).lower()
    for keyword, verdict in VERDICT_KEYWORDS.items():
        if keyword in text:
            return verdict
    return "Unverified"

def ingest_rss():
    for source in SOURCES:
        print(f"📡 Fetching from {source['name']}...")
        feed = feedparser.parse(source["url"])

        for entry in feed.entries:
            claim_text = clean_html(entry.get("title", ""))
            summary = clean_html(entry.get("summary", ""))
            link = entry.get("link", "")
            date_published = entry.get("published", datetime.utcnow().isoformat())

            verdict = extract_verdict(claim_text, summary)

            if not claim_text.strip():
                continue

            embedding = get_embedding(claim_text)
            insert_claim(claim_text, verdict, link, date_published)

            print(f"✅ Inserted: {claim_text[:70]}... [{verdict}]")

if __name__ == "__main__":
    ingest_rss()
    print("🚀 RSS ingestion complete!")
