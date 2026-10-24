"""Tests for atomic transaction boundaries, rollback behavior, and DB constraint enforcement."""
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.attendance.models import Attendance, AttendanceStatus
from app.events.models import Event, EventType
from app.registrations import crud
from app.registrations.models import Registration
from app.registrations.schemas import RegistrationCreate


def _make_event(db_session, **overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        event_code=f"INT-{uuid.uuid4().hex[:8]}",
        slug=f"int-{uuid.uuid4().hex[:8]}",
        name="Integrity Event",
        type=EventType.workshop,
        min_team_size=1,
        max_team_size=4,
        is_active=True,
        reg_open_at=now,
    )
    defaults.update(overrides)
    event = Event(**defaults)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_atomic_creation_inserts_registration_and_attendance(db_session):
    event = _make_event(db_session)
    data = RegistrationCreate(
        team_name="Atomic Team",
        participants=[
            {"name": "Lead", "email": "lead@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Member", "email": "member@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    )

    reg, ev, norm = crud.create_registration(db_session, event.slug, data)

    # Verify registration exists
    saved_reg = db_session.get(Registration, reg.id)
    assert saved_reg is not None
    assert saved_reg.p1_email == "lead@example.com"
    assert saved_reg.p2_email == "member@example.com"
    assert saved_reg.p3_name is None

    # Verify corresponding attendance record exists and is linked
    saved_att = db_session.scalar(select(Attendance).where(Attendance.registration_id == reg.id))
    assert saved_att is not None
    assert saved_att.event_id == event.id
    assert saved_att.status == AttendanceStatus.not_checked_in


def test_atomic_rollback_on_attendance_failure(db_session):
    event = _make_event(db_session)
    data = RegistrationCreate(
        team_name="Rollback Team",
        participants=[
            {"name": "Lead", "email": "failtest@example.com", "phone": "+919876543210", "is_team_lead": True},
        ],
    )

    # Force an error during the transaction by mocking db.add on the second call (attendance)
    real_add = db_session.add

    def failing_add(instance):
        if isinstance(instance, Attendance):
            raise RuntimeError("Simulated DB failure during attendance insert")
        real_add(instance)

    with patch.object(db_session, "add", side_effect=failing_add):
        with pytest.raises(RuntimeError):
            crud.create_registration(db_session, event.slug, data)

    # Verify that registration was rolled back and does not exist
    orphan_reg = db_session.scalar(select(Registration).where(Registration.p1_email == "failtest@example.com"))
    assert orphan_reg is None


def test_invalid_email_rejected():
    with pytest.raises(Exception):
        RegistrationCreate(
            participants=[
                {"name": "Alice", "email": "invalid-email-format", "phone": "+919876543210", "is_team_lead": True}
            ]
        )


def test_invalid_phone_rejected():
    # E.164 pattern requires + followed by 8-15 digits
    with pytest.raises(Exception):
        RegistrationCreate(
            participants=[
                {"name": "Alice", "email": "alice@example.com", "phone": "12345", "is_team_lead": True}
            ]
        )


def test_empty_required_rejected():
    # Empty name (min_length=1)
    with pytest.raises(Exception):
        RegistrationCreate(
            participants=[
                {"name": "", "email": "alice@example.com", "phone": "+919876543210", "is_team_lead": True}
            ]
        )


def test_empty_optional_ignored(db_session):
    event = _make_event(db_session, min_team_size=1, max_team_size=4)
    # Only 2 participants in a 4-person max event — optional slots 3 and 4 are omitted
    data = RegistrationCreate(
        team_name="Duo Team",
        participants=[
            {"name": "Lead", "email": "lead@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Member", "email": "member@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    )
    reg, _, _ = crud.create_registration(db_session, event.slug, data)
    assert reg.p1_name == "Lead"
    assert reg.p2_name == "Member"
    assert reg.p3_name is None
    assert reg.p3_email is None
    assert reg.p4_name is None
    assert reg.p4_email is None
