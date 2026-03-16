import os
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

# ── Configuration (override via environment variables) ─────────────────────────
SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "CHANGE-ME-to-a-long-random-string-in-production-never-commit-real-secrets",
)
ALGORITHM: str = "HS256"
ACCESS_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_EXPIRE_MINUTES", "30"))
REFRESH_EXPIRE_DAYS: int = int(os.getenv("REFRESH_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token helpers ──────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload.update(
        {"exp": datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES), "type": "access"}
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload.update(
        {"exp": datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS), "type": "refresh"}
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError on any validation failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
