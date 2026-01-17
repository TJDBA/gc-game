"""
Database configuration and session management for Galactic Conquest.

This module provides:
- SQLAlchemy Base class for ORM models
- Database engine configuration
- Session factory for database operations
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL from environment variable with fallback for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gc_user:gc_password@localhost:5432/galactic_conquest"
)

# Create SQLAlchemy engine
# pool_pre_ping ensures connections are validated before use
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL query logging during development
)

# Session factory
# autocommit=False: Transactions must be explicitly committed
# autoflush=False: Objects are not automatically flushed to DB
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency generator for FastAPI endpoints.
    
    Usage:
        @app.get("/example")
        def example_endpoint(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: A SQLAlchemy session that is automatically closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()