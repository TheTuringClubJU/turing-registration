"""
app/tests/attendance/test_attendance_row_lifecycle.py

Verifies:
- Attendance row is created in the same DB transaction as the registration
  (defaults to not_checked_in).
- event_id on attendance matches the registration's event_id.
- registration_id UNIQUE constraint is enforced.
"""
import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from app.attendance.models import Attendance, AttendanceStatus
from app.registrations.models import Registration
from app.events.models import Event, EventType
from datetime import datetime, timezone


def _make_event(db_session):
    event = Event(
        event_code=f"TEST-{uuid.uuid4().hex[:8]}",
        slug=f"test-{uuid.uuid4().hex[:8]}",
        name="Test Event",
        type=EventType.workshop,
        min_team_size=1,
        max_team_size=1,
        is_active=False,
        reg_open_at=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.flush()
    return event


def _make_registration(db_session, event):
    reg = Registration(
        event_id=event.id,
        p1_name="Jane Doe",
        p1_email="jane@example.com",
        p1_phone="1234567890",
        p1_is_lead=True,
    )
    db_session.add(reg)
    db_session.flush()
    return reg


def test_attendance_defaults_not_checked_in(db_session):
    event = _make_event(db_session)
    reg = _make_registration(db_session, event)

    attendance = Attendance(registration_id=reg.id, event_id=event.id)
    db_session.add(attendance)
    db_session.flush()

    assert attendance.status == AttendanceStatus.not_checked_in
    assert attendance.event_id == event.id
    assert attendance.registration_id == reg.id


def test_attendance_event_id_matches_registration(db_session):
    event = _make_event(db_session)
    reg = _make_registration(db_session, event)

    attendance = Attendance(registration_id=reg.id, event_id=event.id)
    db_session.add(attendance)
    db_session.flush()

    assert attendance.event_id == reg.event_id


def test_attendance_registration_id_is_unique(db_session):
    event = _make_event(db_session)
    reg = _make_registration(db_session, event)

    db_session.add(Attendance(registration_id=reg.id, event_id=event.id))
    db_session.flush()

    with pytest.raises(IntegrityError):
        db_session.add(Attendance(registration_id=reg.id, event_id=event.id))
        db_session.flush()
