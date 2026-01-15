import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .db import Base


def _uuid():
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

class Game(Base):
    __tablename__ = "games"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    host_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    join_code_hash = Column(String(255), nullable=False)
    started = Column(Boolean, nullable=False, default=False)
    turn_timeout_seconds = Column(Integer, nullable=False, default=86400)
    current_turn = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Player(Base):
    __tablename__ = "players"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    display_name = Column(String(80), nullable=False)     # shown in UI
    faction_name = Column(String(80), nullable=False)     # per-game faction name
    is_host = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("game_id", "user_id", name="uq_players_game_user"),
        UniqueConstraint("game_id", "faction_name", name="uq_players_game_faction"),
    )


class Turn(Base):
    __tablename__ = "turns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PLANNING")  # PLANNING|RESOLVING|RESOLVED
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("game_id", "number", name="uq_turns_game_number"),
    )


class TurnSubmission(Base):
    __tablename__ = "turn_submissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("turns.id"), nullable=False, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    submitted = Column(Boolean, nullable=False, default=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("turn_id", "player_id", name="uq_turn_submissions_turn_player"),
    )


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("turns.id"), nullable=False, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    kind = Column(String(50), nullable=False)             # fleet_move, fleet_split, etc.
    target_type = Column(String(20), nullable=False)      # fleet|hex|system|player
    target_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("turn_id", "player_id", "kind", "target_id", name="uq_orders_turn_player_kind_target"),
    )
