import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.schemas.auth_schema import MessageResponse, RefreshRequest, TokenResponse, UserLogin, UserRegister
from app.services.auth_service import authenticate_user, refresh_access_token, register_user
from app.utils.csrf import generate_csrf_token
from app.utils.database import get_db
from app.utils.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "service": "auth"}


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit("5/minute")
def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)):
    """
    Create a new user account.

    - Passwords are validated for strength before hashing with bcrypt.
    - Duplicate emails return 400 without leaking which email already exists.
    - Rate-limited to **5 requests / minute** per IP.
    """
    user = register_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )
    return MessageResponse(message="Account created successfully.", user_id=user.id)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive tokens",
)
@limiter.limit("10/minute")
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    """
    Validate credentials and return a JWT access token + refresh token pair.

    - A CSRF token is included in the response for browser-based clients.
    - Rate-limited to **10 requests / minute** per IP.
    - Invalid credentials always return 401 (no user enumeration).
    """
    result = authenticate_user(db, payload.email, payload.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = result
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        csrf_token=generate_csrf_token(),
    )


@router.post(
    "/refresh",
    summary="Obtain a new access token using a refresh token",
)
@limiter.limit("20/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new short-lived access token.

    The refresh token must match the one stored in the database (single-use
    rotation strategy prevents token reuse after logout).
    """
    new_access_token = refresh_access_token(db, payload.refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": new_access_token, "token_type": "bearer"}
