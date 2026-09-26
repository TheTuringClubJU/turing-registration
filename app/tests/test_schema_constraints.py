"""
app/tests/test_schema_constraints.py

Tests the DB-level constraints defined in schema.sql / mirrored in
events/models.py, registrations/models.py, attendance/models.py.

These test the schema itself — not business logic (that's participant
count rules, duplicate email checks, etc. which belong in
registrations/validators.py and its own tests, once that's built).

Requires schema.sql to already be applied to the test database.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.events.models import Event, EventType
from app.registrations.models import Registration
from app.attendance.models import Attendance, Organiser, AttendanceStatus, CheckinMethod


def make_event(**overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        event_code=f"TEST-{uuid.uuid4().hex[:8]}",
        slug=f"test-{uuid.uuid4().hex[:8]}",
        name="Test Event",
        type=EventType.workshop,
        min_team_size=1,
        max_team_size=1,
        is_active=False,
        reg_open_at=now,
    )
    defaults.update(overrides)
    return Event(**defaults)


# ------------------------------------------------------------------
# events constraints
# ------------------------------------------------------------------

class TestEventConstraints:
    def test_min_team_size_le_max_team_size_enforced_at_creation(self, db_session):
        event = make_event(min_team_size=4, max_team_size=1)
        db_session.add(event)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_min_team_size_must_be_positive(self, db_session):
        event = make_event(min_team_size=0, max_team_size=1)
        db_session.add(event)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_close_after_open_constraint(self, db_session):
        now = datetime.now(timezone.utc)
        event = make_event(reg_open_at=now, reg_close_at=now - timedelta(days=1))
        db_session.add(event)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_valid_event_is_accepted(self, db_session):
        event = make_event(min_team_size=1, max_team_size=4)
        db_session.add(event)
        db_session.flush()  # should not raise
        assert event.id is not None

    def test_only_one_active_event_at_a_time(self, db_session):
        event_a = make_event(is_active=True)
        db_session.add(event_a)
        db_session.flush()

        event_b = make_event(is_active=True)
        db_session.add(event_b)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_event_code_must_be_unique(self, db_session):
        shared_code = f"DUPLICATE-{uuid.uuid4().hex[:8]}"
        event_a = make_event(event_code=shared_code)
        db_session.add(event_a)
        db_session.flush()

        event_b = make_event(event_code=shared_code)
        db_session.add(event_b)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_slug_must_be_unique(self, db_session):
        shared_slug = f"dup-slug-{uuid.uuid4().hex[:8]}"
        event_a = make_event(slug=shared_slug)
        db_session.add(event_a)
        db_session.flush()

        event_b = make_event(slug=shared_slug)
        db_session.add(event_b)
        with pytest.raises(IntegrityError):
            db_session.flush()


# ------------------------------------------------------------------
# registrations constraints
# ------------------------------------------------------------------

class TestRegistrationConstraints:
    def test_registration_requires_event_id(self, db_session):
        registration = Registration(
            p1_name="Jane Doe",
            p1_email="jane@example.com",
            p1_phone="1234567890",
        )
        db_session.add(registration)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_valid_solo_registration_is_accepted(self, db_session):
        event = make_event(min_team_size=1, max_team_size=1)
        db_session.add(event)
        db_session.flush()

        registration = Registration(
            event_id=event.id,
            p1_name="Jane Doe",
            p1_email="jane@example.com",
            p1_phone="1234567890",
            p1_is_lead=True,
        )
        db_session.add(registration)
        db_session.flush()  # should not raise
        assert registration.id is not None

    def test_participant_slots_helper_skips_empty_slots(self, db_session):
        event = make_event(min_team_size=1, max_team_size=4)
        db_session.add(event)
        db_session.flush()

        registration = Registration(
            event_id=event.id,
            team_name="Team Test",
            p1_name="Lead Person",
            p1_email="lead@example.com",
            p1_phone="1111111111",
            p1_is_lead=True,
            p2_name="Second Person",
            p2_email="second@example.com",
            p2_phone="2222222222",
        )
        db_session.add(registration)
        db_session.flush()

        slots = registration.participant_slots()
        assert len(slots) == 2
        assert slots[0]["name"] == "Lead Person"
        assert slots[1]["name"] == "Second Person"


# ------------------------------------------------------------------
# attendance / organisers constraints
# ------------------------------------------------------------------

class TestAttendanceConstraints:
    def _make_registration(self, db_session, **event_overrides):
        event = make_event(**event_overrides)
        db_session.add(event)
        db_session.flush()

        registration = Registration(
            event_id=event.id,
            p1_name="Jane Doe",
            p1_email="jane@example.com",
            p1_phone="1234567890",
            p1_is_lead=True,
        )
        db_session.add(registration)
        db_session.flush()
        return event, registration

    def test_attendance_defaults_not_checked_in(self, db_session):
        event, registration = self._make_registration(db_session)

        attendance = Attendance(registration_id=registration.id, event_id=event.id)
        db_session.add(attendance)
        db_session.flush()

        assert attendance.status == AttendanceStatus.not_checked_in
        assert attendance.method is None
        assert attendance.checked_in_at is None
        assert attendance.checked_in_by is None

    def test_registration_id_unique_on_attendance(self, db_session):
        event, registration = self._make_registration(db_session)

        db_session.add(Attendance(registration_id=registration.id, event_id=event.id))
        db_session.flush()

        with pytest.raises(IntegrityError):
            db_session.add(Attendance(registration_id=registration.id, event_id=event.id))
            db_session.flush()

    def test_checkin_fields_must_be_consistent_partial_set_rejected(self, db_session):
        event, registration = self._make_registration(db_session)

        # method set but checked_in_at / checked_in_by left null — should violate
        # the checkin_fields_consistent CHECK constraint
        attendance = Attendance(
            registration_id=registration.id,
            event_id=event.id,
            method=CheckinMethod.qr,
        )
        db_session.add(attendance)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_checkin_fields_all_set_together_is_accepted(self, db_session):
        event, registration = self._make_registration(db_session)

        organiser = Organiser(
            email=f"organiser-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="not-a-real-hash",
            name="Test Organiser",
        )
        db_session.add(organiser)
        db_session.flush()

        attendance = Attendance(
            registration_id=registration.id,
            event_id=event.id,
            status=AttendanceStatus.checked_in,
            method=CheckinMethod.manual,
            checked_in_at=datetime.now(timezone.utc),
            checked_in_by=organiser.id,
        )
        db_session.add(attendance)
        db_session.flush()  # should not raise
        assert attendance.id is not None

    def test_organiser_email_must_be_unique(self, db_session):
        shared_email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
        db_session.add(Organiser(email=shared_email, password_hash="x", name="A"))
        db_session.flush()

        with pytest.raises(IntegrityError):
            db_session.add(Organiser(email=shared_email, password_hash="y", name="B"))
            db_session.flush()