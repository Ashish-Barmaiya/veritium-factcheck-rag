# server/app/ingestion/scrape_snope.py

import requests
from bs4 import BeautifulSoup
from app.services.embedding_service import get_embedding
from app.services.db_service import insert_claim

BASE_URL = "https://www.snopes.com/fact-check/page/{}/"

def scrape_snopes(max_pages=50):
    for page in range(1, max_pages + 1):
        print(f"Scraping Snopes page {page}...")
        resp = requests.get(BASE_URL.format(page))
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = soup.select("article.media-wrapper")
        if not articles:
            break

        for article in articles:
            title_tag = article.select_one("h2.title a")
            verdict_tag = article.select_one(".media-rating")
            date_tag = article.select_one("time")

            claim_text = title_tag.text.strip() if title_tag else None
            link = title_tag["href"] if title_tag else None
            verdict = verdict_tag.text.strip() if verdict_tag else "Unverified"
            date_published = date_tag["datetime"] if date_tag else None

            if not claim_text:
                continue

            embedding = get_embedding(claim_text)
            insert_claim(claim_text, verdict, link, date_published, embedding)

if __name__ == "__main__":
    scrape_snopes(max_pages=200)
