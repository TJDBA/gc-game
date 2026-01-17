"""
Galactic Conquest Backend Application Package.

This package contains:
- db: Database configuration and session management
- models: SQLAlchemy ORM models for all game entities
"""

from .db import Base, SessionLocal, get_db, engine
from .models import (
    # Enums
    GameStatus,
    SystemClass,
    ShipType,
    StanceType,
    NeutralDisposition,
    ScanBand,
    EventType,
    # Auth models
    User,
    Session,
    # Game core models
    Game,
    Player,
    Turn,
    TurnSubmission,
    Order,
    # Map state models
    System,
    Fleet,
    Ship,
    Population,
    # Tech & diplomacy models
    TechLevels,
    Stance,
    FirstContact,
    # Scan & event models
    ScanSnapshot,
    ScanVisibility,
    EventLog,
)

__all__ = [
    # Database
    "Base",
    "SessionLocal",
    "get_db",
    "engine",
    # Enums
    "GameStatus",
    "SystemClass",
    "ShipType",
    "StanceType",
    "NeutralDisposition",
    "ScanBand",
    "EventType",
    # Auth models
    "User",
    "Session",
    # Game core models
    "Game",
    "Player",
    "Turn",
    "TurnSubmission",
    "Order",
    # Map state models
    "System",
    "Fleet",
    "Ship",
    "Population",
    # Tech & diplomacy models
    "TechLevels",
    "Stance",
    "FirstContact",
    # Scan & event models
    "ScanSnapshot",
    "ScanVisibility",
    "EventLog",
]
