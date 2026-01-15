from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session as OrmSession

from .db import SessionLocal
from .models import Session as DbSession, User
from .security import pwd_context

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_user(
    authorization: Optional[str] = Header(default=None),
    db: OrmSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    sessions = db.query(DbSession).all()
    for s in sessions:
        if pwd_context.verify(token, s.token_hash):
            user = db.query(User).filter(User.id == s.user_id).first()
            if user:
                return user

    raise HTTPException(status_code=401, detail="Invalid token")
