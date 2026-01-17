"""
Database configuration for Galactic Conquest.

Provides:
- Base: Declarative base for all ORM models
- engine: SQLAlchemy engine instance
- SessionLocal: Session factory for creating database sessions
- get_db(): FastAPI dependency for request-scoped sessions
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://gc_user:gc_password@localhost:5432/galactic_conquest"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()