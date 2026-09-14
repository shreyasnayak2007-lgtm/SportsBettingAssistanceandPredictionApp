import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    if engine is None:
        raise RuntimeError('DATABASE_URL or POSTGRES_URL is required for database-backed routes')
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
