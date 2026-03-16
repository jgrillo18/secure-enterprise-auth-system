from __future__ import annotations

import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)


def register_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Create a new user account.

    Returns the created User or None if the email is already taken.
    """
    if db.query(User).filter(User.email == email).first():
        logger.warning("Registration attempt with existing email: %s", email)
        return None

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: id=%s", user.id)
    return user


def authenticate_user(
    db: Session, email: str, password: str
) -> Optional[Tuple[str, str]]:
    """
    Validate credentials and issue JWT + refresh token pair.

    Returns (access_token, refresh_token) on success, None on failure.
    """
    user = db.query(User).filter(User.email == email).first()

    # Intentionally identical error path to prevent user enumeration
    if not user or not verify_password(password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", email)
        return None

    if not user.is_active:
        logger.warning("Inactive user attempted login: id=%s", user.id)
        return None

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    user.refresh_token = refresh_token
    db.commit()

    logger.info("Successful login: id=%s", user.id)
    return access_token, refresh_token


def refresh_access_token(db: Session, refresh_token: str) -> Optional[str]:
    """
    Validate a stored refresh token and issue a new access token.

    Returns a new access_token or None if the token is invalid / revoked.
    """
    from jose import JWTError
    from app.utils.security import decode_token

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            return None
        email: str = payload.get("sub", "")
    except JWTError:
        logger.warning("Invalid refresh token received.")
        return None

    user = db.query(User).filter(User.email == email).first()
    if not user or user.refresh_token != refresh_token:
        logger.warning("Refresh token mismatch for email: %s", email)
        return None

    return create_access_token({"sub": user.email})
