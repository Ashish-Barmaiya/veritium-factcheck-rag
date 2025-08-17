# server/app/ingestion/scrape_afp.py

import requests
from bs4 import BeautifulSoup
from app.services.embedding_service import get_embedding
from app.services.db_service import insert_claim

BASE_URL = "https://factcheck.afp.com/facts?page={}"

def scrape_afp(max_pages=50):
    for page in range(1, max_pages + 1):
        print(f"Scraping AFP Fact Check page {page}...")
        resp = requests.get(BASE_URL.format(page))
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = soup.select("div.teaser__body")
        if not articles:
            break

        for article in articles:
            title_tag = article.select_one("h3.teaser__title a")
            claim_text = title_tag.text.strip() if title_tag else None
            link = "https://factcheck.afp.com" + title_tag["href"] if title_tag else None
            verdict_tag = article.select_one("span.verdict")  # adjust selector
            verdict = verdict_tag.text.strip() if verdict_tag else "Unverified"
            date_tag = article.select_one("time.teaser__date")
            date_published = date_tag["datetime"] if date_tag else None

            if not claim_text:
                continue

            embedding = get_embedding(claim_text)
            insert_claim(claim_text, verdict, link, date_published, embedding)

if __name__ == "__main__":
    scrape_afp(max_pages=50)
