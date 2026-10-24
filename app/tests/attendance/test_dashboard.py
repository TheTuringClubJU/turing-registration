"""
app/tests/attendance/test_dashboard.py

Tests for get_summary and get_list CRUD functions.
"""
import uuid
from datetime import datetime, timezone

from app.attendance import crud
from app.attendance.models import Attendance, AttendanceStatus, CheckinMethod, Organiser
from app.events.models import Event, EventType
from app.registrations.models import Registration


def _ev(db, active=False):
    ev = Event(
        event_code=f"D-{uuid.uuid4().hex[:8]}",
        slug=f"d-{uuid.uuid4().hex[:8]}",
        name="Dash Event",
        type=EventType.seminar,
        min_team_size=1,
        max_team_size=1,
        is_active=active,
        reg_open_at=datetime.now(timezone.utc),
    )
    db.add(ev); db.flush()
    return ev


def _reg(db, event):
    r = Registration(
        event_id=event.id,
        p1_name="Bob",
        p1_email=f"bob-{uuid.uuid4().hex[:6]}@example.com",
        p1_phone="1111111111",
        p1_is_lead=True,
    )
    db.add(r); db.flush()
    return r


def _att(db, reg, event):
    a = Attendance(registration_id=reg.id, event_id=event.id)
    db.add(a); db.flush()
    return a


def _org(db):
    o = Organiser(
        email=f"org-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="x",
        name="Organiser",
    )
    db.add(o); db.flush()
    return o


def test_summary_counts_correct(db_session):
    ev = _ev(db_session)
    r1, r2, r3 = _reg(db_session, ev), _reg(db_session, ev), _reg(db_session, ev)
    a1, a2, a3 = _att(db_session, r1, ev), _att(db_session, r2, ev), _att(db_session, r3, ev)

    org = _org(db_session)
    # Check in only first two
    a1.status = AttendanceStatus.checked_in
    a1.method = CheckinMethod.qr
    a1.checked_in_at = datetime.now(timezone.utc)
    a1.checked_in_by = org.id
    a2.status = AttendanceStatus.checked_in
    a2.method = CheckinMethod.manual
    a2.checked_in_at = datetime.now(timezone.utc)
    a2.checked_in_by = org.id
    db_session.flush()

    summary = crud.get_summary(db_session, ev.id)
    assert summary["total_registered"] == 3
    assert summary["checked_in"] == 2
    assert summary["remaining"] == 1


def test_list_returns_all_registrations(db_session):
    ev = _ev(db_session)
    r1, r2 = _reg(db_session, ev), _reg(db_session, ev)
    _att(db_session, r1, ev)
    _att(db_session, r2, ev)

    rows = crud.get_list(db_session, ev.id)
    assert len(rows) == 2


def test_list_scoped_to_event_id(db_session):
    ev1, ev2 = _ev(db_session), _ev(db_session)
    r1, r2 = _reg(db_session, ev1), _reg(db_session, ev2)
    _att(db_session, r1, ev1)
    _att(db_session, r2, ev2)

    rows_ev1 = crud.get_list(db_session, ev1.id)
    assert len(rows_ev1) == 1
    assert rows_ev1[0]["event_id"] == str(ev1.id)
