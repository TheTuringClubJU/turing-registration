"""
app/core/security.py

Organiser authentication: password hashing, JWT issue/verify,
and the FastAPI dependency that protects every attendance route.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.schemas import LoginRequest, TokenResponse

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _create_token(organiser_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(organiser_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)


def _decode_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
        return UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ---------------------------------------------------------------------------
# FastAPI dependency — protects every organiser-only route
# ---------------------------------------------------------------------------


def require_valid_organiser(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Dependency that decodes the Bearer JWT and returns the matching
    Organiser ORM object.  Raises 401 if the token is missing/expired/invalid
    or if the organiser no longer exists in the database.
    """
    # Import here to avoid circular imports (attendance.models → core.database → core.security)
    from app.attendance.models import Organiser

    organiser_id = _decode_token(token)
    organiser = db.get(Organiser, organiser_id)
    if organiser is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organiser not found")
    return organiser


# keep the old name as an alias so existing code that imported get_current_organiser still works
get_current_organiser = require_valid_organiser


# ---------------------------------------------------------------------------
# Login router (mounted in main.py)
# ---------------------------------------------------------------------------

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Accepts organiser email + password, returns a Bearer JWT on success.
    Registered organisers are inserted manually into the DB for now.
    """
    from app.attendance.models import Organiser
    from sqlalchemy import select

    email = payload.identifier
    organiser = db.scalar(select(Organiser).where(Organiser.username == email))
    if organiser is None or not verify_password(payload.password, organiser.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = _create_token(organiser.id)
    return TokenResponse(access_token=token, token_type="bearer")

