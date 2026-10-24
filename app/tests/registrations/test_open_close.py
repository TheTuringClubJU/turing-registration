"""Tests for event active state and time window boundaries in registration."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.events.models import Event, EventType
from app.registrations import crud
from app.registrations.schemas import RegistrationCreate


def _build_event(db_session, **overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        event_code=f"TIME-{uuid.uuid4().hex[:8]}",
        slug=f"time-{uuid.uuid4().hex[:8]}",
        name="Time Window Event",
        type=EventType.workshop,
        min_team_size=1,
        max_team_size=1,
        is_active=True,
        reg_open_at=now - timedelta(hours=1),
        reg_close_at=now + timedelta(hours=1),
    )
    defaults.update(overrides)
    event = Event(**defaults)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_inactive_event_rejects_registration(db_session):
    event = _build_event(db_session, is_active=False)
    data = RegistrationCreate(
        participants=[{"name": "Solo", "email": "solo@example.com", "phone": "+919876543210", "is_team_lead": True}]
    )
    with pytest.raises(crud.EventClosedError):
        crud.create_registration(db_session, event.slug, data)


def test_registration_before_opening_rejected(db_session):
    now = datetime.now(timezone.utc)
    # Opens tomorrow
    event = _build_event(
        db_session,
        reg_open_at=now + timedelta(days=1),
        reg_close_at=now + timedelta(days=2),
    )
    data = RegistrationCreate(
        participants=[{"name": "Early", "email": "early@example.com", "phone": "+919876543210", "is_team_lead": True}]
    )
    with pytest.raises(crud.EventClosedError):
        crud.create_registration(db_session, event.slug, data)


def test_registration_after_closing_rejected(db_session):
    now = datetime.now(timezone.utc)
    # Closed an hour ago
    event = _build_event(
        db_session,
        reg_open_at=now - timedelta(days=2),
        reg_close_at=now - timedelta(hours=1),
    )
    data = RegistrationCreate(
        participants=[{"name": "Late", "email": "late@example.com", "phone": "+919876543210", "is_team_lead": True}]
    )
    with pytest.raises(crud.EventClosedError):
        crud.create_registration(db_session, event.slug, data)


def test_registration_within_open_window_succeeds(db_session):
    now = datetime.now(timezone.utc)
    event = _build_event(
        db_session,
        reg_open_at=now - timedelta(minutes=30),
        reg_close_at=now + timedelta(minutes=30),
    )
    data = RegistrationCreate(
        participants=[{"name": "OnTime", "email": "ontime@example.com", "phone": "+919876543210", "is_team_lead": True}]
    )
    reg, _, _ = crud.create_registration(db_session, event.slug, data)
    assert reg.id is not None
