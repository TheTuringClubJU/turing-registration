"""
app/registrations/crud.py

Transactional registration operations.
Owns transaction boundary for atomic creation of Registration and Attendance rows.
Locks the event row (SELECT ... FOR UPDATE) to prevent race conditions during
concurrent email uniqueness checks.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.attendance.models import Attendance, AttendanceStatus
from app.events.models import Event
from app.events.policy import registration_is_open
from app.registrations.models import Registration, RegistrationStatus
from app.registrations.schemas import RegistrationCreate
from app.registrations.validators import validate_registration

logger = logging.getLogger(__name__)


class EventNotFoundError(Exception):
    """Event slug does not exist."""


class EventClosedError(Exception):
    """Event is not active or registration window is closed."""


class DuplicateEmailError(Exception):
    """Email already registered for this event."""


def get_registration_by_id(db: Session, registration_id: UUID) -> Registration | None:
    return db.get(Registration, registration_id)


def get_registrations_by_event(db: Session, event_id: UUID) -> list[Registration]:
    return list(db.scalars(select(Registration).where(Registration.event_id == event_id)).all())


def create_registration(
    db: Session,
    event_slug: str,
    data: RegistrationCreate,
) -> tuple[Registration, Event, RegistrationCreate]:
    """
    Atomically registers participants for an event:
    1. Loads and locks event row (`SELECT ... FOR UPDATE`) to serialize registrations.
    2. Enforces active status and registration time window (`registration_is_open`).
    3. Runs pure validation (`validate_registration`) for slot and lead rules.
    4. Verifies no participant email is already registered in active registrations for this event.
    5. Inserts Registration and Attendance (status='not_checked_in') rows in one single transaction.
    6. Commits both rows atomically or rolls back both on any failure.
    """
    try:
        # Step 1: Load and lock event row
        event = db.scalar(
            select(Event).where(Event.slug == event_slug).with_for_update()
        )
        if event is None:
            raise EventNotFoundError(f"Event '{event_slug}' not found")

        # Step 2: Enforce active / opening window policy
        if not registration_is_open(event):
            raise EventClosedError(f"Registration for event '{event_slug}' is closed")

        # Step 3: Run pure validation
        normalized = validate_registration(data, event)

        # Step 4: Duplicate-email prevention across p1-p4 slots for this event.
        # Cancelled registrations do not block re-registration.
        incoming_emails = [p.email.lower() for p in normalized.participants]
        existing_regs = db.scalars(
            select(Registration).where(
                Registration.event_id == event.id,
                Registration.status == RegistrationStatus.registered,
            )
        ).all()

        for existing_reg in existing_regs:
            for slot in existing_reg.participant_slots():
                reg_email = (slot["email"] or "").strip().lower()
                if reg_email in incoming_emails:
                    raise DuplicateEmailError(
                        f"Email '{reg_email}' is already registered for this event"
                    )

        # Step 5: Map request slots to database columns
        slots_kwargs = {}
        for i in range(1, 5):
            if i <= len(normalized.participants):
                p = normalized.participants[i - 1]
                slots_kwargs[f"p{i}_name"] = p.name
                slots_kwargs[f"p{i}_email"] = p.email
                slots_kwargs[f"p{i}_phone"] = p.phone
                slots_kwargs[f"p{i}_is_lead"] = p.is_team_lead
            else:
                slots_kwargs[f"p{i}_name"] = None
                slots_kwargs[f"p{i}_email"] = None
                slots_kwargs[f"p{i}_phone"] = None
                slots_kwargs[f"p{i}_is_lead"] = False

        registration = Registration(
            event_id=event.id,
            team_name=normalized.team_name,
            status=RegistrationStatus.registered,
            **slots_kwargs,
        )
        db.add(registration)
        db.flush()

        # Step 6: Create Attendance record in the same transaction
        attendance = Attendance(
            registration_id=registration.id,
            event_id=event.id,
            status=AttendanceStatus.not_checked_in,
        )
        db.add(attendance)

        db.commit()
        db.refresh(registration)
        return registration, event, normalized

    except Exception:
        db.rollback()
        raise
