# server/app/ingestion/ingest_all.py

from app.ingestion.scrape_snope import scrape_snopes
from app.ingestion.scrape_boomlive import scrape_boomlive
from app.ingestion.scrape_altnews import scrape_altnews
from app.ingestion.scrape_politifact import scrape_politifact
from app.ingestion.scrape_factcheck_org import scrape_factcheck_org
from app.ingestion.scrape_afp import scrape_afp

def ingest_all():
    print("Starting ingestion from all sources...\n")

    print("1. Snopes")
    scrape_snopes(max_pages=50)
    
    print("2. BoomLive")
    scrape_boomlive(max_pages=50)
    
    print("3. AltNews")
    scrape_altnews(max_pages=50)
    
    print("4. PolitiFact")
    scrape_politifact(max_pages=50)
    
    print("5. FactCheck.org")
    scrape_factcheck_org(max_pages=50)
    
    print("6. AFP Fact Check")
    scrape_afp(max_pages=50)

    print("\nIngestion completed!")

if __name__ == "__main__":
    ingest_all()
