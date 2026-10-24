"""
app/tests/attendance/test_auth.py

Tests for core/security.py:
- hash_password + verify_password round-trip
- _create_token + _decode_token round-trip
- expired token is rejected
- missing/invalid token raises HTTPException 401
"""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from app.core.security import (
    hash_password,
    verify_password,
    _create_token,
    _decode_token,
    _ALGORITHM,
)
from app.core.config import settings


def test_password_hash_and_verify():
    plain = "super-secret-password"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_round_trip():
    organiser_id = uuid.uuid4()
    token = _create_token(organiser_id)
    decoded_id = _decode_token(token)
    assert decoded_id == organiser_id


def test_expired_token_raises_401():
    organiser_id = uuid.uuid4()
    # Forge an already-expired token
    payload = {"sub": str(organiser_id), "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}
    expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        _decode_token(expired_token)
    assert exc_info.value.status_code == 401


def test_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        _decode_token("this-is-not-a-valid-jwt")
    assert exc_info.value.status_code == 401
