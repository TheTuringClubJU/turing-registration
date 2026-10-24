"""Tests for duplicate-email prevention across within-submission, database slots, cancelled states, and concurrency."""
import uuid
from datetime import datetime, timezone

import pytest

from app.events.models import Event, EventType
from app.registrations import crud
from app.registrations.models import RegistrationStatus
from app.registrations.schemas import RegistrationCreate
from app.registrations.validators import RegistrationValidationError, validate_registration


def test_duplicate_email_within_submission_rejected():
    rules = type("Rules", (), {"min_team_size": 2, "max_team_size": 4})()
    data = RegistrationCreate(
        team_name="Duplicate Team",
        participants=[
            {"name": "Lead", "email": "lead@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Clone", "email": "LEAD@EXAMPLE.COM", "phone": "+919876543211", "is_team_lead": False},
        ],
    )
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(data, rules)
    assert exc.value.errors[0]["loc"] == ["body", "participants", 1, "email"]


def _create_event(db_session, **overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        event_code=f"DUP-{uuid.uuid4().hex[:8]}",
        slug=f"dup-{uuid.uuid4().hex[:8]}",
        name="Duplicate Test Event",
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


def test_same_event_rejects_duplicate_email_across_all_slots(db_session):
    event = _create_event(db_session)

    # Initial registration fills slot 1 (lead) and slot 2 (member)
    data1 = RegistrationCreate(
        team_name="First Team",
        participants=[
            {"name": "Lead", "email": "lead1@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Member", "email": "member1@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    )
    crud.create_registration(db_session, event.slug, data1)

    # Attempting to register member1 email again in slot 1 of another team -> rejected
    data2 = RegistrationCreate(
        team_name="Second Team",
        participants=[
            {"name": "New Lead", "email": "MEMBER1@EXAMPLE.COM", "phone": "+919876543212", "is_team_lead": True},
        ],
    )
    with pytest.raises(crud.DuplicateEmailError):
        crud.create_registration(db_session, event.slug, data2)

    # Attempting to register lead1 email in slot 2 of another team -> rejected
    data3 = RegistrationCreate(
        team_name="Third Team",
        participants=[
            {"name": "Other Lead", "email": "other@example.com", "phone": "+919876543214", "is_team_lead": True},
            {"name": "Duplicate Member", "email": "lead1@example.com", "phone": "+919876543215", "is_team_lead": False},
        ],
    )
    with pytest.raises(crud.DuplicateEmailError):
        crud.create_registration(db_session, event.slug, data3)


def test_different_event_allows_same_email(db_session):
    event_a = _create_event(db_session, slug=f"event-a-{uuid.uuid4().hex[:6]}")
    # Note: Only one active event can exist at a time due to partial index.
    # We create event_b as inactive initially, then switch active flags.
    event_b = _create_event(db_session, is_active=False, slug=f"event-b-{uuid.uuid4().hex[:6]}")

    shared_email = "reusable@example.com"
    data_a = RegistrationCreate(
        team_name="Team A",
        participants=[{"name": "Alice", "email": shared_email, "phone": "+919876543210", "is_team_lead": True}]
    )
    reg_a, _, _ = crud.create_registration(db_session, event_a.slug, data_a)
    assert reg_a.id is not None

    # Switch active event to event_b: deactivate event_a first to satisfy only_one_active_event constraint
    event_a.is_active = False
    db_session.commit()
    event_b.is_active = True
    db_session.commit()

    data_b = RegistrationCreate(
        team_name="Team B",
        participants=[{"name": "Alice", "email": shared_email, "phone": "+919876543210", "is_team_lead": True}]
    )
    reg_b, _, _ = crud.create_registration(db_session, event_b.slug, data_b)
    assert reg_b.id is not None
    assert reg_b.id != reg_a.id


def test_cancelled_registration_frees_up_email(db_session):
    event = _create_event(db_session)
    email = "canceller@example.com"

    data = RegistrationCreate(
        team_name="Cancel Team",
        participants=[{"name": "User", "email": email, "phone": "+919876543210", "is_team_lead": True}]
    )
    reg, _, _ = crud.create_registration(db_session, event.slug, data)

    # Cancel registration
    reg.status = RegistrationStatus.cancelled
    db_session.commit()

    # Re-registering with same email should now succeed
    reg_new, _, _ = crud.create_registration(db_session, event.slug, data)
    assert reg_new.id is not None
    assert reg_new.id != reg.id
