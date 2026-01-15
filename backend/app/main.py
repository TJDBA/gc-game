from typing import Optional, List
import datetime
import uuid

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import User, Session as DbSession, Game, Player, Turn, TurnSubmission, Order
from .security import hash_password, verify_password, new_token, hash_join_code, verify_join_code, pwd_context
from .auth import require_user

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------
# Schemas
# ------------------

class SignupIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=200)

class LoginIn(BaseModel):
    username: str
    password: str

class LoginOut(BaseModel):
    token: str

class GameCreateIn(BaseModel):
    name: str
    join_code: str = Field(min_length=4, max_length=32)
    turn_timeout_seconds: int = 86400

class GameCreateOut(BaseModel):
    game_id: uuid.UUID

class GameJoinIn(BaseModel):
    join_code: str
    display_name: str
    faction_name: str

class GameJoinOut(BaseModel):
    player_id: uuid.UUID

class MyGameOut(BaseModel):
    game_id: uuid.UUID
    name: str
    started: bool
    current_turn: int
    player_id: uuid.UUID
    display_name: str
    faction_name: str
    is_host: bool


# ------------------
# Health
# ------------------

@app.get("/health")
def health():
    return {"ok": True}


# ------------------
# Auth
# ------------------

@app.post("/auth/signup")
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="username already exists")

    u = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(u)
    db.commit()
    return {"ok": True}

@app.post("/auth/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == payload.username).first()
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = new_token()
    token_hash = pwd_context.hash(token)

    s = DbSession(user_id=u.id, token_hash=token_hash)
    db.add(s)
    db.commit()
    return LoginOut(token=token)


# ------------------
# Games
# ------------------

@app.get("/games", response_model=List[MyGameOut])
def list_my_games(db: Session = Depends(get_db), user: User = Depends(require_user)):
    rows = (
        db.query(Game, Player)
        .join(Player, Player.game_id == Game.id)
        .filter(Player.user_id == user.id)
        .all()
    )
    out = []
    for g, p in rows:
        out.append(MyGameOut(
            game_id=g.id,
            name=g.name,
            started=g.started,
            current_turn=g.current_turn,
            player_id=p.id,
            display_name=p.display_name,
            faction_name=p.faction_name,
            is_host=p.is_host,
        ))
    return out

@app.post("/games", response_model=GameCreateOut)
def create_game(payload: GameCreateIn, db: Session = Depends(get_db), user: User = Depends(require_user)):
    g = Game(
        name=payload.name,
        host_user_id=user.id,
        join_code_hash=hash_join_code(payload.join_code),
        turn_timeout_seconds=payload.turn_timeout_seconds,
        started=False,
        current_turn=1,
    )
    db.add(g)
    db.flush()

    # host becomes a player immediately
    p = Player(
        game_id=g.id,
        user_id=user.id,
        display_name=user.username,
        faction_name=f"{user.username}'s Faction",
        is_host=True,
    )
    db.add(p)

    # create turn 1
    t = Turn(game_id=g.id, number=1, status="PLANNING")
    db.add(t)

    db.commit()
    return GameCreateOut(game_id=g.id)

@app.post("/games/{game_id}/join", response_model=GameJoinOut)
def join_game(game_id: uuid.UUID, payload: GameJoinIn, db: Session = Depends(get_db), user: User = Depends(require_user)):
    g = db.query(Game).filter(Game.id == game_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="game not found")
    if g.started:
        raise HTTPException(status_code=400, detail="game already started")

    if not verify_join_code(payload.join_code, g.join_code_hash):
        raise HTTPException(status_code=401, detail="invalid join code")

    existing = db.query(Player).filter(Player.game_id == g.id, Player.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="already joined")

    p = Player(
        game_id=g.id,
        user_id=user.id,
        display_name=payload.display_name,
        faction_name=payload.faction_name,
        is_host=False,
    )
    db.add(p)
    db.commit()
    return GameJoinOut(player_id=p.id)
