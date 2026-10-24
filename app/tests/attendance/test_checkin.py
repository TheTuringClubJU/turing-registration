"""
app/tests/attendance/test_checkin.py

Tests for mark_attended CRUD function:
- qr scan marks checked_in with method=qr
- manual marks with method=manual
- duplicate check-in is idempotent
- invalid registration_id → LookupError (404 at router level)
- checked_in_by records correct organiser UUID
"""
import uuid
from datetime import datetime, timezone

import pytest

from app.attendance import crud
from app.attendance.models import Attendance, AttendanceStatus, CheckinMethod, Organiser
from app.events.models import Event, EventType
from app.registrations.models import Registration


def _make_event(db):
    ev = Event(
        event_code=f"T-{uuid.uuid4().hex[:8]}",
        slug=f"t-{uuid.uuid4().hex[:8]}",
        name="Checkin Event",
        type=EventType.workshop,
        min_team_size=1,
        max_team_size=1,
        is_active=False,
        reg_open_at=datetime.now(timezone.utc),
    )
    db.add(ev); db.flush()
    return ev


def _make_registration(db, event):
    reg = Registration(
        event_id=event.id,
        p1_name="Alice",
        p1_email="alice@example.com",
        p1_phone="0000000000",
        p1_is_lead=True,
    )
    db.add(reg); db.flush()
    return reg


def _make_organiser(db):
    org = Organiser(
        email=f"org-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed",
        name="Test Organiser",
    )
    db.add(org); db.flush()
    return org


def _seed(db):
    ev = _make_event(db)
    reg = _make_registration(db, ev)
    att = Attendance(registration_id=reg.id, event_id=ev.id)
    db.add(att); db.flush()
    org = _make_organiser(db)
    return ev, reg, att, org


def test_qr_scan_marks_checked_in(db_session):
    ev, reg, att, org = _seed(db_session)
    result = crud.mark_attended(db_session, reg.id, CheckinMethod.qr, org.id)
    assert result.status == AttendanceStatus.checked_in
    assert result.method == CheckinMethod.qr
    assert result.checked_in_by == org.id


def test_manual_marks_checked_in(db_session):
    ev, reg, att, org = _seed(db_session)
    result = crud.mark_attended(db_session, reg.id, CheckinMethod.manual, org.id)
    assert result.status == AttendanceStatus.checked_in
    assert result.method == CheckinMethod.manual


def test_duplicate_checkin_is_idempotent(db_session):
    ev, reg, att, org = _seed(db_session)
    first = crud.mark_attended(db_session, reg.id, CheckinMethod.qr, org.id)
    second = crud.mark_attended(db_session, reg.id, CheckinMethod.manual, org.id)
    # Second call returns the original record unchanged
    assert second.status == AttendanceStatus.checked_in
    assert second.method == CheckinMethod.qr   # unchanged from first


def test_invalid_registration_id_raises_lookup_error(db_session):
    with pytest.raises(LookupError):
        crud.mark_attended(db_session, uuid.uuid4(), CheckinMethod.qr, uuid.uuid4())


def test_checked_in_by_records_correct_organiser(db_session):
    ev, reg, att, org = _seed(db_session)
    result = crud.mark_attended(db_session, reg.id, CheckinMethod.qr, org.id)
    assert result.checked_in_by == org.id
