import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def new_token() -> str:
    # random bearer token; store only hashed form in DB later (next block)
    return secrets.token_urlsafe(32)

def hash_join_code(code: str) -> str:
    # join codes are short; still hash so DB leaks don’t expose active join codes
    return pwd_context.hash(code)

def verify_join_code(code: str, code_hash: str) -> bool:
    return pwd_context.verify(code, code_hash)
