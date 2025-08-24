# server/app/services/db_service.py
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError
from app.config import PG_DB_URL, QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME
from app.services.embedding_service import get_embedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)

# --- SQLAlchemy and PostgreSQL Setup ---
Base = declarative_base()

class ClaimModel(Base):
    """ORM model for the 'claims' table in PostgreSQL."""
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_text = Column(Text, nullable=False, unique=True)
    verdict = Column(String(255))
    source_url = Column(String(2048), nullable=False, unique=True)
    published_date = Column(Date)
    version = Column(Integer, default=1)  # Versioning for optimistic locking
    short_points = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(PG_DB_URL, pool_size=10, max_overflow=20)
Session = sessionmaker(bind=engine)

# --- Qdrant Setup ---
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def init_dbs():
    """Initializes both PostgreSQL and Qdrant databases."""
    try:
        logger.info("Initializing PostgreSQL tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL tables initialized.")
    except OperationalError as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise  # Re-raise to stop execution if DB isn't available

    try:
        logger.info("Initializing Qdrant collection...")
        collections = qdrant_client.get_collections().collections
        if COLLECTION_NAME not in [c.name for c in collections]:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
        logger.info("Qdrant collection initialized.")
    except UnexpectedResponse as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        raise

# --- New Combined Insertion Function ---
def insert_claim_with_vector(text, verdict, source_url, short_points, date):
    """
    Inserts a claim only if it doesn't already exist in the database.
    Returns True on successful insertion, False otherwise.
    """
    db_session = Session()
    try:
        # Check if claim already exists
        existing_claim = db_session.query(ClaimModel).filter(
            (ClaimModel.source_url == source_url) | (ClaimModel.claim_text == text)
        ).first()

        if existing_claim:
            logger.info(f"Duplicate entry found: {source_url} or claim '{text[:50]}...'. Skipping.")
            return False

        # Insert into Postgres
        published_date = datetime.fromisoformat(date).date() if date else None
        new_claim = ClaimModel(
            claim_text=text,
            verdict=verdict,
            source_url=source_url,
            short_points="\n".join(short_points) if short_points else None,
            published_date=published_date
        )
        db_session.add(new_claim)
        db_session.commit()
        db_session.refresh(new_claim)

        logger.info(f"Successfully inserted into PostgreSQL. ID: {new_claim.id}")

        # Prepare text for embedding (include short_points if available)
        embedding_input = text
        if short_points:
            embedding_input += "\n" + " ".join(short_points)

        embedding = get_embedding(embedding_input)

        # Insert into Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=new_claim.id,
                    vector=embedding,
                    payload={
                        "text": text,
                        "verdict": verdict,
                        "source_url": source_url,
                        "date": date,
                        "short_points": short_points,
                    }
                )
            ]
        )
        logger.info(f"Successfully inserted into Qdrant with ID: {new_claim.id}")
        return True

    except IntegrityError:
        db_session.rollback()
        logger.warning(f"Integrity error (race condition) on {source_url}. Skipping.")
        return False
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to insert claim {source_url}: {e}")
        return False
    finally:
        db_session.close()

# Call the initialization function when the module is loaded
init_dbs()

def search_claim(query_embedding, top_k=1):
    """Searches Qdrant and returns the results."""
    results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True
    )
    return results
