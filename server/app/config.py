import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "veritium-v1")

HF_API_KEY = os.getenv("HF_API_KEY")

PG_DB_URL = os.getenv("PG_DB_URL")

SLEEP_BETWEEN_REQUESTS = float(os.getenv("SCRAPER_SLEEP_BETWEEN_RETRIES"))
MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES"))
REQUEST_TIMEOUT = int(os.getenv("SCRAPER_REQUEST_TIMEOUT"))