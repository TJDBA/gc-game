"""
SQLAlchemy models for Galactic Conquest MVP.

This module defines all ORM models matching the gc_mvp_001 + gc_mvp_002 schema.
Models are organized into logical groups:
- Auth: User, Session
- Game Core: Game, Player, Turn, TurnSubmission, Order
- Map State: System, Fleet, Ship, Population
- Tech & Diplomacy: TechLevels, Stance, FirstContact
- Scanning: ScanSnapshot, ScanVisibility
- Events: EventLog

Important: Index declarations in __table_args__ must match the database indexes
created in gc_mvp_001 exactly (same names, same columns) for alembic check to pass.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, BigInteger, DateTime, Boolean,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .db import Base


def _uuid():
    """Generate a new UUID4."""
    return uuid.uuid4()


# =============================================================================
# ENUMS
# =============================================================================

class GameStatus(str, Enum):
    """Game lifecycle states."""
    LOBBY = "LOBBY"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class SystemClass(str, Enum):
    """Star system classifications (A=best, E=worst)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class ShipType(str, Enum):
    """Ship type classifications."""
    SCOUT = "SCOUT"
    CRUISER = "CRUISER"
    BATTLESHIP = "BATTLESHIP"
    TRANSPORT = "TRANSPORT"


class StanceType(str, Enum):
    """Diplomatic stance options."""
    HOSTILE = "HOSTILE"
    NEUTRAL = "NEUTRAL"
    FRIENDLY = "FRIENDLY"


class NeutralDisposition(str, Enum):
    """Neutral population behavior types."""
    HOSTILE = "HOSTILE"
    FRIENDLY = "FRIENDLY"
    DEFENSIVE = "DEFENSIVE"


class ScanBand(str, Enum):
    """Scan visibility bands (SHORT=best detail, LONG=least detail)."""
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class EventType(str, Enum):
    """Game event types for the event log."""
    GAME_STARTED = "GAME_STARTED"
    TURN_RESOLVED = "TURN_RESOLVED"
    FLEET_MOVED = "FLEET_MOVED"
    COMBAT_OCCURRED = "COMBAT_OCCURRED"
    SYSTEM_CAPTURED = "SYSTEM_CAPTURED"
    POPULATION_CHANGED = "POPULATION_CHANGED"
    TECH_PURCHASED = "TECH_PURCHASED"
    PLAYER_ELIMINATED = "PLAYER_ELIMINATED"
    FIRST_CONTACT = "FIRST_CONTACT"
    FLEET_SPLIT = "FLEET_SPLIT"
    FLEET_MERGED = "FLEET_MERGED"
    SHIP_BUILT = "SHIP_BUILT"
    POPULATION_LOADED = "POPULATION_LOADED"
    POPULATION_UNLOADED = "POPULATION_UNLOADED"
    STANCE_CHANGED = "STANCE_CHANGED"
    TAXES_PAID = "TAXES_PAID"
    POPULATION_REDUCED = "POPULATION_REDUCED"


class TurnStatus(str, Enum):
    """Turn processing status."""
    PLANNING = "PLANNING"
    RESOLVING = "RESOLVING"
    RESOLVED = "RESOLVED"


class EventVisibility(str, Enum):
    """Who can see an event in the event log."""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    PLAYER_ONLY = "PLAYER_ONLY"


# =============================================================================
# AUTH MODELS
# =============================================================================

class User(Base):
    """User account for authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    hosted_games = relationship("Game", back_populates="host_user", foreign_keys="Game.host_user_id")
    players = relationship("Player", back_populates="user")


class Session(Base):
    """Bearer token session for authenticated API access."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")


# =============================================================================
# GAME CORE MODELS
# =============================================================================

class Game(Base):
    """
    A game instance containing players, systems, fleets, and turns.
    
    Lifecycle: LOBBY -> ACTIVE -> FINISHED
    """
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    host_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    join_code_hash = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default=GameStatus.LOBBY.value)
    rng_seed = Column(BigInteger, nullable=False, default=0)
    turn_timeout_seconds = Column(Integer, nullable=False, default=86400)
    current_turn = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    host_user = relationship("User", back_populates="hosted_games", foreign_keys=[host_user_id])
    players = relationship("Player", back_populates="game", cascade="all, delete-orphan")
    turns = relationship("Turn", back_populates="game", cascade="all, delete-orphan")
    systems = relationship("System", back_populates="game", cascade="all, delete-orphan")
    fleets = relationship("Fleet", back_populates="game", cascade="all, delete-orphan")
    first_contacts = relationship("FirstContact", back_populates="game", cascade="all, delete-orphan")
    event_logs = relationship("EventLog", back_populates="game", cascade="all, delete-orphan")

    @property
    def started(self) -> bool:
        """Backward-compatible property. True if game is no longer in LOBBY."""
        return self.status != GameStatus.LOBBY.value

    @property
    def game_status(self) -> GameStatus:
        """Return status as enum."""
        return GameStatus(self.status)


class Player(Base):
    """
    A user's participation in a specific game.
    
    Each user can join multiple games with different display/faction names.
    """
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    display_name = Column(String(80), nullable=False)
    faction_name = Column(String(80), nullable=False)
    faction_color = Column(String(7), nullable=False, default="#FFFFFF")
    banked_rp = Column(Integer, nullable=False, default=0)
    home_sextant_q = Column(Integer, nullable=True)
    home_sextant_r = Column(Integer, nullable=True)
    is_host = Column(Boolean, nullable=False, default=False)
    is_eliminated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("game_id", "user_id", name="uq_players_game_user"),
        UniqueConstraint("game_id", "faction_name", name="uq_players_game_faction"),
    )

    # Relationships
    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="players")
    fleets = relationship("Fleet", back_populates="player", cascade="all, delete-orphan")
    populations = relationship("Population", back_populates="player", cascade="all, delete-orphan")
    tech_levels = relationship(
        "TechLevels", 
        back_populates="player", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    stances_as_source = relationship(
        "Stance",
        foreign_keys="Stance.player_id",
        back_populates="player",
        cascade="all, delete-orphan"
    )
    stances_as_target = relationship(
        "Stance",
        foreign_keys="Stance.target_player_id",
        back_populates="target_player"
    )
    scan_visibilities = relationship(
        "ScanVisibility", 
        back_populates="player", 
        cascade="all, delete-orphan"
    )
    turn_submissions = relationship(
        "TurnSubmission",
        back_populates="player",
        cascade="all, delete-orphan"
    )
    orders = relationship(
        "Order",
        back_populates="player",
        cascade="all, delete-orphan"
    )
    first_contacts_initiated = relationship(
        "FirstContact",
        foreign_keys="FirstContact.player_id",
        back_populates="player"
    )
    first_contacts_received = relationship(
        "FirstContact",
        foreign_keys="FirstContact.other_player_id",
        back_populates="other_player"
    )
    event_logs = relationship("EventLog", back_populates="player")


class Turn(Base):
    """
    A single turn in a game's progression.
    
    Status flow: PLANNING -> RESOLVING -> RESOLVED
    """
    __tablename__ = "turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PLANNING")
    rng_seed = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("game_id", "number", name="uq_turns_game_number"),
    )

    # Relationships
    game = relationship("Game", back_populates="turns")
    submissions = relationship("TurnSubmission", back_populates="turn", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="turn", cascade="all, delete-orphan")
    scan_snapshots = relationship("ScanSnapshot", back_populates="turn", cascade="all, delete-orphan")

    @property
    def turn_status(self) -> TurnStatus:
        """Return status as enum."""
        return TurnStatus(self.status)


class TurnSubmission(Base):
    """Tracks whether a player has submitted their orders for a turn."""
    __tablename__ = "turn_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"), nullable=False, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted = Column(Boolean, nullable=False, default=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("turn_id", "player_id", name="uq_turn_submissions_turn_player"),
    )

    # Relationships
    turn = relationship("Turn", back_populates="submissions")
    player = relationship("Player", back_populates="turn_submissions")


class Order(Base):
    """
    A player's order for a specific turn.
    
    Orders are UPSERT-ed by (turn_id, player_id, kind, target_id).
    target_type indicates the entity type being targeted (FLEET, SYSTEM, PLAYER, NONE).
    target_id references the specific entity UUID (required, NOT NULL).
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"), nullable=False, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(50), nullable=False)
    target_type = Column(String(20), nullable=False)  # FLEET, SYSTEM, PLAYER, NONE
    target_id = Column(UUID(as_uuid=True), nullable=False)  # Always required
    payload = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("turn_id", "player_id", "kind", "target_id", name="uq_orders_turn_player_kind_target"),
    )

    # Relationships
    turn = relationship("Turn", back_populates="orders")
    player = relationship("Player", back_populates="orders")


# =============================================================================
# MAP STATE MODELS
# =============================================================================

class System(Base):
    """
    A star system on the hex map.
    
    Systems generate RP when controlled. Class determines base value (A=best).
    """
    __tablename__ = "systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    hex_q = Column(Integer, nullable=False)
    hex_r = Column(Integer, nullable=False)
    system_class = Column(String(1), nullable=False)
    rp_value = Column(Integer, nullable=False)
    neutral_pop_tenths = Column(Integer, nullable=False, default=0)
    neutral_disposition = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("game_id", "hex_q", "hex_r", name="uq_systems_game_hex"),
        # Index name must match DB: ix_systems_game_hex
        Index('ix_systems_game_hex', 'game_id', 'hex_q', 'hex_r'),
    )

    # Relationships
    game = relationship("Game", back_populates="systems")
    populations = relationship("Population", back_populates="system", cascade="all, delete-orphan")

    @property
    def hex_coords(self) -> tuple:
        """Return hex coordinates as a tuple."""
        return (self.hex_q, self.hex_r)

    @property
    def system_class_enum(self) -> SystemClass:
        """Return system_class as enum."""
        return SystemClass(self.system_class)

    @property
    def neutral_disposition_enum(self):
        """Return neutral_disposition as enum, or None."""
        if self.neutral_disposition is None:
            return None
        return NeutralDisposition(self.neutral_disposition)


class Fleet(Base):
    """
    A container for ships owned by a player at a hex location.
    
    Fleets can carry population via cargo_pop_tenths on transports.
    """
    __tablename__ = "fleets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    hex_q = Column(Integer, nullable=False)
    hex_r = Column(Integer, nullable=False)
    cargo_pop_tenths = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Index names must match DB
        Index('ix_fleets_game_player', 'game_id', 'player_id'),
        Index('ix_fleets_game_hex', 'game_id', 'hex_q', 'hex_r'),
    )

    # Relationships
    game = relationship("Game", back_populates="fleets")
    player = relationship("Player", back_populates="fleets")
    ships = relationship("Ship", back_populates="fleet", cascade="all, delete-orphan")

    @property
    def hex_coords(self) -> tuple:
        """Return hex coordinates as a tuple."""
        return (self.hex_q, self.hex_r)

    @property
    def ship_count(self) -> int:
        """Return total number of ships in fleet."""
        return len(self.ships)

    @property
    def is_empty(self) -> bool:
        """Return True if fleet has no ships."""
        return len(self.ships) == 0

    @property
    def cargo_population(self) -> float:
        """Return cargo population as a float (e.g., 1.5 instead of 15 tenths)."""
        return self.cargo_pop_tenths / 10.0


class Ship(Base):
    """
    An individual ship within a fleet.
    
    Ship types: SCOUT, CRUISER, BATTLESHIP, TRANSPORT
    """
    __tablename__ = "ships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    fleet_id = Column(UUID(as_uuid=True), ForeignKey("fleets.id", ondelete="CASCADE"), nullable=False)
    ship_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Index name must match DB
        Index('ix_ships_fleet', 'fleet_id'),
    )

    # Relationships
    fleet = relationship("Fleet", back_populates="ships")

    @property
    def ship_type_enum(self) -> ShipType:
        """Return ship_type as enum."""
        return ShipType(self.ship_type)


class Population(Base):
    """
    Player population at a star system.
    
    Population is tracked in tenths (10 = 1.0 pop).
    Control requires >= 0.5 pop and >= 2x other factions combined.
    """
    __tablename__ = "populations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    system_id = Column(UUID(as_uuid=True), ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    pop_tenths = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("system_id", "player_id", name="uq_populations_system_player"),
        # Index names must match DB
        Index('ix_populations_system', 'system_id'),
        Index('ix_populations_player', 'player_id'),
    )

    # Relationships
    system = relationship("System", back_populates="populations")
    player = relationship("Player", back_populates="populations")

    @property
    def population(self) -> float:
        """Return population as a float (e.g., 1.5 instead of 15 tenths)."""
        return self.pop_tenths / 10.0


# =============================================================================
# TECH & DIPLOMACY MODELS
# =============================================================================

class TechLevels(Base):
    """
    Technology progression for a player (one record per player).
    
    Each tech type ranges from 0-5. Affects movement range, combat CV, and scan range.
    
    Tech Effects:
    - Movement: base range + movement_tech
    - Combat: base CV * (1 + combat_tech * 0.1)
    - Scanning: see ScanVisibility for correct range formulas
    """
    __tablename__ = "tech_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True)
    movement_tech = Column(Integer, nullable=False, default=0)
    combat_tech = Column(Integer, nullable=False, default=0)
    scanning_tech = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="tech_levels")

    def as_dict(self) -> dict:
        """Return tech levels as a dictionary."""
        return {
            "movement": self.movement_tech,
            "combat": self.combat_tech,
            "scanning": self.scanning_tech,
        }


class Stance(Base):
    """
    Diplomatic stance from one player toward another.
    
    target_player_id=NULL sets the default stance for unknown players.
    Stances: HOSTILE (triggers combat), NEUTRAL (coexist), FRIENDLY (shared visibility).
    """
    __tablename__ = "stances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    target_player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=True)
    stance = Column(String(20), nullable=False, default=StanceType.NEUTRAL.value)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("player_id", "target_player_id", name="uq_stances_player_target"),
        # Index name must match DB
        Index('ix_stances_player', 'player_id'),
    )

    # Relationships
    player = relationship(
        "Player", 
        foreign_keys=[player_id], 
        back_populates="stances_as_source"
    )
    target_player = relationship(
        "Player", 
        foreign_keys=[target_player_id],
        back_populates="stances_as_target"
    )

    @property
    def stance_type(self) -> StanceType:
        """Return stance as enum."""
        return StanceType(self.stance)

    @property
    def is_default_stance(self) -> bool:
        """Return True if this is the default stance (no specific target)."""
        return self.target_player_id is None


class FirstContact(Base):
    """
    Records when two players first encounter each other.
    
    Used for event logging and potential diplomatic mechanics.
    """
    __tablename__ = "first_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    other_player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    hex_q = Column(Integer, nullable=False)
    hex_r = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("game_id", "player_id", "other_player_id", name="uq_first_contacts_players"),
    )

    # Relationships
    game = relationship("Game", back_populates="first_contacts")
    player = relationship(
        "Player", 
        foreign_keys=[player_id],
        back_populates="first_contacts_initiated"
    )
    other_player = relationship(
        "Player", 
        foreign_keys=[other_player_id],
        back_populates="first_contacts_received"
    )

    @property
    def hex_coords(self) -> tuple:
        """Return hex coordinates as a tuple."""
        return (self.hex_q, self.hex_r)


# =============================================================================
# SCAN & VISIBILITY MODELS
# =============================================================================

class ScanSnapshot(Base):
    """
    Records the complete state of a hex at the end of a turn.
    
    One record per (turn_id, hex_q, hex_r). Contains full hex state in JSONB.
    The contents field represents the **end-of-turn canonical state** after all
    turn phases have resolved (post-resolution).
    
    Visibility filtering happens via ScanVisibility lookup.
    
    Contents JSONB structure:
    {
        "system": {
            "id": "uuid",
            "system_class": "B",
            "rp_value": 7,
            "controller_id": "player-uuid",
            "contested": false,
            "populations": [{"player_id": "uuid", "pop_tenths": 15}],
            "neutral_pop_tenths": 0
        },
        "fleets": [
            {
                "id": "uuid",
                "player_id": "uuid",
                "ships": [{"id": "uuid", "ship_type": "CRUISER"}],
                "cargo_pop_tenths": 0
            }
        ]
    }
    """
    __tablename__ = "scan_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"), nullable=False)
    hex_q = Column(Integer, nullable=False)
    hex_r = Column(Integer, nullable=False)
    contents = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("turn_id", "hex_q", "hex_r", name="uq_scan_snapshots_turn_hex"),
        # Index names must match DB
        Index('ix_scan_snapshots_turn', 'turn_id'),
        Index('ix_scan_snapshots_turn_hex', 'turn_id', 'hex_q', 'hex_r'),
    )

    # Relationships
    turn = relationship("Turn", back_populates="scan_snapshots")
    visibilities = relationship("ScanVisibility", back_populates="scan_snapshot", cascade="all, delete-orphan")

    @property
    def hex_coords(self) -> tuple:
        """Return hex coordinates as a tuple."""
        return (self.hex_q, self.hex_r)

    @property
    def has_system(self) -> bool:
        """Return True if this hex contains a system."""
        return self.contents.get("system") is not None

    @property
    def has_fleets(self) -> bool:
        """Return True if this hex contains any fleets."""
        return len(self.contents.get("fleets", [])) > 0


class ScanVisibility(Base):
    """
    Per-player fog-of-war lookup.
    
    Links players to hex snapshots with their best scan band.
    Only the best band (SHORT > MEDIUM > LONG) per player+snapshot is stored.
    
    **Uniqueness Guarantee:** The unique constraint on (scan_snapshot_id, player_id)
    ensures exactly ONE best-band record per player per hex per turn. Since 
    scan_snapshot_id uniquely identifies a (turn_id, hex_q, hex_r) tuple, this
    provides the required best-band-per-player-per-hex-per-turn invariant.
    
    Scan Band Priority:
    - SHORT: Full details (populations, ship composition, cargo)
    - MEDIUM: Partial details (controller, strength bands)
    - LONG: Presence only (system class, fleet owner)
    
    Scan Range Formulas (scan_base = 1 + scanning_tech):
    - LONG range:   scan_base × 2
    - MEDIUM range: scan_base
    - SHORT range:  floor(scanning_tech / 2)  [0 at tech 0-1 = same-hex only]
    
    Query pattern for fog of war:
        SELECT ss.hex_q, ss.hex_r, ss.contents, sv.scan_band
        FROM scan_snapshots ss
        JOIN scan_visibility sv ON sv.scan_snapshot_id = ss.id
        WHERE sv.player_id = :player_id
          AND ss.turn_id = :turn_id;
    """
    __tablename__ = "scan_visibility"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    scan_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("scan_snapshots.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    scan_band = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("scan_snapshot_id", "player_id", name="uq_scan_visibility_snapshot_player"),
        # Index names must match DB
        Index('ix_scan_visibility_snapshot', 'scan_snapshot_id'),
        Index('ix_scan_visibility_player', 'player_id'),
    )

    # Relationships
    scan_snapshot = relationship("ScanSnapshot", back_populates="visibilities")
    player = relationship("Player", back_populates="scan_visibilities")

    @property
    def scan_band_enum(self) -> ScanBand:
        """Return scan_band as enum."""
        return ScanBand(self.scan_band)

    # Convenience properties to access snapshot data without explicit join
    @property
    def turn_id(self):
        """Return turn_id from the associated snapshot."""
        return self.scan_snapshot.turn_id

    @property
    def hex_q(self) -> int:
        """Return hex_q from the associated snapshot."""
        return self.scan_snapshot.hex_q

    @property
    def hex_r(self) -> int:
        """Return hex_r from the associated snapshot."""
        return self.scan_snapshot.hex_r

    @property
    def hex_coords(self) -> tuple:
        """Return hex coordinates as a tuple from the associated snapshot."""
        return self.scan_snapshot.hex_coords


# =============================================================================
# EVENT LOGGING
# =============================================================================

class EventLog(Base):
    """
    Records game events for replay and debugging.
    
    Events include combat, movement, captures, tech purchases, etc.
    Visibility controls who can see each event: PUBLIC, PRIVATE, PLAYER_ONLY.
    """
    __tablename__ = "event_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSONB, nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    visibility = Column(String(20), nullable=False, default="PUBLIC")
    hex_q = Column(Integer, nullable=True)
    hex_r = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Index names must match DB
        Index('ix_event_log_game_turn', 'game_id', 'turn_number'),
        Index('ix_event_log_game_type', 'game_id', 'event_type'),
    )

    # Relationships
    game = relationship("Game", back_populates="event_logs")
    player = relationship("Player", back_populates="event_logs")

    @property
    def event_type_enum(self) -> EventType:
        """Return event_type as enum."""
        return EventType(self.event_type)

    @property
    def visibility_enum(self) -> EventVisibility:
        """Return visibility as enum."""
        return EventVisibility(self.visibility)

    @property
    def hex_coords(self):
        """Return hex coordinates as a tuple, or None if not location-specific."""
        if self.hex_q is not None and self.hex_r is not None:
            return (self.hex_q, self.hex_r)
        return None