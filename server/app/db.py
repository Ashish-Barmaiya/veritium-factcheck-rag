from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import PG_DB_URL

engine = create_engine(PG_DB_URL, pool_size=10, max_overflow=20)
Session = sessionmaker(bind=engine)
