# server/app/ingestion/scrape_politifact.py

import requests
from bs4 import BeautifulSoup
from app.services.embedding_service import get_embedding
from app.services.db_service import insert_claim

BASE_URL = "https://www.politifact.com/factchecks/list/?page={}"

def scrape_politifact(max_pages=50):
    for page in range(1, max_pages + 1):
        print(f"Scraping PolitiFact page {page}...")
        resp = requests.get(BASE_URL.format(page))
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = soup.select("li.o-listicle__item")
        if not articles:
            break

        for article in articles:
            title_tag = article.select_one("div.m-statement__quote")
            claim_text = title_tag.text.strip() if title_tag else None
            link_tag = article.select_one("a.m-statement__quote__link")
            link = "https://www.politifact.com" + link_tag["href"] if link_tag else None
            verdict_tag = article.select_one("div.m-statement__meter span")  # adjust if needed
            verdict = verdict_tag.text.strip() if verdict_tag else "Unverified"
            date_tag = article.select_one("footer.m-statement__footer time")
            date_published = date_tag["datetime"] if date_tag else None

            if not claim_text:
                continue

            embedding = get_embedding(claim_text)
            insert_claim(claim_text, verdict, link, date_published, embedding)

if __name__ == "__main__":
    scrape_politifact(max_pages=50)
