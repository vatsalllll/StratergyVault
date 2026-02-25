"""
StrategyVault - Database Dependency
Provides FastAPI-compatible session management and startup hooks.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from src.core.config import settings
from src.models.database import Base


# Create engine — use check_same_thread=False for SQLite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and auto-closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
