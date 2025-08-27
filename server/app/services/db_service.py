# server/app/services/db_service.py
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError
from app.config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME
from app.services.embedding_service import get_embedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from qdrant_client.http.exceptions import UnexpectedResponse
from app.models import Base, ClaimModel, Source, Actor, Entity, ClaimEntity
from app.db import engine, Session
from app.utils.compute_simhash import compute_simhash, SIMHASH_THRESHOLD

logger = logging.getLogger(__name__)

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

# --- Old Combined Insertion Function ---
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


# --- Combined Insertion Function v2 (Updated) ---
def insert_claim_with_vector_v2(
    text: str, 
    verdict: str, 
    source_url: str, 
    short_points: list[str] | None, 
    date: str | None, # ISO string
    entities_data: list[dict] | None = None,
    fact_checker_platform: str = 'fact_checker', # Default, can be overridden
    fact_checker_handle: str | None = None,      # Dynamic handle
    fact_checker_display_name: str | None = None # Dynamic display name
):
    """
    Inserts claims after checking for deduplication using simhash.
    Also extracts and inserts entities.
    Returns True on successful insertion, False otherwise.
    
    Args:
        text: The claim text.
        verdict: The verdict from the fact-checker.
        source_url: The URL of the fact-check article.
        short_points: A list of short summary points (if any).
        date: The publication date as an ISO string.
        entities_data: A list of dicts with 'name', 'kind', 'lang' for entities.
        fact_checker_platform: The platform type (e.g., 'fact_checker', 'news').
        fact_checker_handle: The unique handle/identifier for the fact-checker (e.g., 'snopes', 'politifact').
        fact_checker_display_name: The display name of the fact-checker (e.g., 'Snopes', 'PolitiFact').
    """
    db_session = Session()

    try:
        # --- Step 1: compute simhash for the new claim ---
        claim_hash = compute_simhash(text)

        # --- Step 2: Deduplication check (claim-level) ---
        # Note: Fetching all simhashes is inefficient for large DBs.
        # Consider optimizing with PostgreSQL bitwise ops or a dedicated service later.
        existing_claims_simhashes = db_session.query(ClaimModel.simhash).all()\
        
        # Convert the new claim's hash (string) to int for comparison
        current_claim_hash_int = int(claim_hash)

        for ec_tuple in existing_claims_simhashes: # Query returns tuples
            ec_simhash_str = ec_tuple.simhash # Access the simhash string attribute
            if ec_simhash_str is None:
                continue
            try:
                # Convert existing claim's simhash to int
                ec_simhash = int(ec_simhash_str)
                # Calculate Hamming distance
                distance = bin(current_claim_hash_int ^ ec_simhash).count("1")
                if distance <= SIMHASH_THRESHOLD:
                    logger.info(f"Near-duplicate claim found (Hamming={distance}). Skipping insert for '{text[:50]}...'.")
                    db_session.close()
                    return False # Duplicate found, do not insert
            except ValueError:
                logger.warning(f"Stored simhash '{ec_simhash_str}' is not a valid integer. Skipping comparison for this entry.")
                continue

        # --- Step 3: Prepare data for insertion ---
        published_date = None
        if date:
            try:
                # Parse the ISO date string 
                # Snopes uses format like "2024-11-15T16:30:00+00:00" or "2024-11-15T16:30:00Z"
                dt_obj = datetime.fromisoformat(date.rstrip('Z')) # Remove 'Z' suffix if present before parsing
                published_date = dt_obj.date()
            except ValueError:
                logger.warning(f"Could not parse date '{date}' for URL {source_url}. Setting published_date to None.")

        # --- Step 4: Handle Source ---
        from urllib.parse import urlparse
        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc.lower()
        
        # Get or create the Source object
        # Assume source name is derived from domain or passed, defaulting to domain for now
        source = db_session.query(Source).filter(Source.domain == domain, Source.kind == 'fact_checker').first()
        if not source:
            # Use domain as default name, or pass a name if known from scraper context
            source_name_default = domain.replace("www.", "").split('.')[0].title() 
            source = Source(
                domain=domain, 
                kind='fact_checker', 
                name= source_name_default # You might want to pass this dynamically too
            )
            db_session.add(source)
            db_session.flush() # Get the source ID without committing
        source_id = source.id

        # --- Step 5: Handle Fact Checker Actor (Dynamically) ---
        # The handle is now passed as an argument
        if not fact_checker_handle:
             logger.error("fact_checker_handle is required but was not provided.")
             return False # Or raise an exception

        # Get or create the Actor object for the fact-checker
        fact_checker = db_session.query(Actor).filter(
            Actor.platform == fact_checker_platform, 
            Actor.handle == fact_checker_handle
        ).first()
        
        if not fact_checker:
            # Create new actor. Use display_name if provided, otherwise default to handle/title
            display_name_to_use = fact_checker_display_name or fact_checker_handle.title()
            fact_checker = Actor(
                platform=fact_checker_platform, 
                handle=fact_checker_handle, 
                display_name=display_name_to_use, 
                source_id=source_id # Link to the source
            )
            db_session.add(fact_checker)
            db_session.flush() # Get the actor ID
        fact_checker_id = fact_checker.id

        # --- Step 6: Create Claim object ---
        new_claim = ClaimModel(
            claim_text=text,
            verdict=verdict,
            source_url=source_url,
            published_date=published_date,
            simhash=claim_hash,
            source_id=source_id,
            fact_checker_id=fact_checker_id,
            language='en', # Default language, could be made dynamic if needed
            short_points="\n".join(short_points) if short_points else None
        )
        db_session.add(new_claim)
        db_session.flush() # Get the claim ID before committing
        claim_id = new_claim.id

        # --- Step 7: Handle Entities ---
        # entities_data is expected to be a list of dicts [{'name': '...', 'kind': '...'}, ...]
        if entities_data:
            for entity_info in entities_data:
                name = entity_info.get('name')
                kind = entity_info.get('kind', 'other')
                lang = entity_info.get('lang', 'en')
                if not name:
                    continue
                # Get or create Entity
                entity = db_session.query(Entity).filter(
                    Entity.name == name, 
                    Entity.kind == kind, 
                    Entity.lang == lang
                ).first()
                if not entity:
                    entity = Entity(name=name, kind=kind, lang=lang)
                    db_session.add(entity)
                    db_session.flush() # Get entity ID
                # Create ClaimEntity link
                claim_entity_link = ClaimEntity(claim_id=claim_id, entity_id=entity.id)
                db_session.add(claim_entity_link)

        # --- Commit to PostgreSQL ---
        db_session.commit()
        logger.info(f"Successfully inserted into PostgreSQL. Claim ID: {claim_id}")

        # --- Step 8: Prepare and Insert into Qdrant ---
        # Prepare text for embedding (include short_points if available)
        embedding_input = text
        if short_points:
            embedding_input += "\n" + "\n".join(short_points) # Join with newlines for better separation
        # Add entities to embedding input if desired (optional enrichment)
        # if entities_data:
        #     entity_names = [e['name'] for e in entities_data]
        #     embedding_input += "\nEntities: " + ", ".join(entity_names)

        try:
            embedding = get_embedding(embedding_input) # Assuming this function exists and returns a list/vector
        except:
            logger.error(f"Failed to generate embedding for claim '{text[:50]}...': {e}")
            return False # Return False immediately if embedding fails  
          
        # Insert into Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=claim_id,
                    vector=embedding,
                    payload={
                        "text": text,
                        "verdict": verdict,
                        "source_url": source_url,
                        "date": date, # Keep original ISO string for Qdrant
                        "short_points": short_points,
                        # --- Add other payload fields if needed --- #

                        # "fact_checker_handle": fact_checker_handle,
                        # "fact_checker_display_name": fact_checker_display_name
                    }
                )
            ]
        )
        logger.info(f"Successfully inserted into Qdrant with ID: {claim_id}")
        return True

    except IntegrityError as e:
        db_session.rollback()
        logger.warning(f"Integrity error (likely duplicate key) on {source_url}: {e}. Skipping.")
        return False 
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to insert claim {source_url}: {e}", exc_info=True) # Log full traceback
        return False
    finally:
        db_session.close()


# Call the initialization function when the module is loaded
# Consider moving this to your application's startup code (e.g., in main.py or __init__.py)
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
