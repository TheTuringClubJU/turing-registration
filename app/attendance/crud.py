from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.attendance.models import Attendance, AttendanceStatus, CheckinMethod

if TYPE_CHECKING:
    from app.registrations.models import Registration as _Registration

try:
    from app.registrations.models import Registration
except ImportError:
    Registration = None  # type: ignore[assignment,misc]


def resolve_registration_id(db: Session, identifier: str) -> UUID | None:
    """
    Resolves an identifier string to a registration UUID.
    Can be:
    1. A valid UUID string
    2. A short ticket code (e.g. 'TTC-A1B2')
    """
    clean = identifier.strip()
    if not clean:
        return None

    # Try UUID parse
    try:
        return UUID(clean)
    except (ValueError, TypeError):
        pass

    # Try ticket_code lookup
    if Registration is not None:
        reg = db.scalar(
            select(Registration).where(
                func.upper(Registration.ticket_code) == clean.upper()
            )
        )
        if reg:
            return reg.id

    return None


def mark_attended(db: Session, identifier: str | UUID, method: CheckinMethod, organiser_id: UUID) -> Attendance:
    """
    Marks a specific registration as checked-in using either UUID or short ticket_code.
    """
    if isinstance(identifier, UUID):
        reg_id = identifier
    else:
        reg_id = resolve_registration_id(db, str(identifier))

    if reg_id is None:
        raise LookupError("Registration not found")

    # Fetch existing attendance record
    stmt = select(Attendance).where(Attendance.registration_id == reg_id)
    attendance = db.scalar(stmt)

    if attendance is None:
        raise LookupError("Registration not found")

    # Idempotency check: If already checked in, return as-is
    if attendance.status == AttendanceStatus.checked_in:
        return attendance

    # Update the record
    attendance.status = AttendanceStatus.checked_in
    attendance.method = method
    attendance.checked_in_at = datetime.now(timezone.utc)
    attendance.checked_in_by = organiser_id

    db.commit()
    db.refresh(attendance)

    return attendance


def get_summary(db: Session, event_id: UUID) -> dict[str, Any]:
    """
    Gets a summary count of attendees for an event.
    """
    total_count = db.scalar(select(func.count(Attendance.id)).where(Attendance.event_id == event_id)) or 0
    checked_in_count = db.scalar(
        select(func.count(Attendance.id)).where(
            Attendance.event_id == event_id,
            Attendance.status == AttendanceStatus.checked_in,
        )
    ) or 0

    return {
        "total_registered": total_count,
        "checked_in": checked_in_count,
        "remaining": total_count - checked_in_count,
    }


def get_list(db: Session, event_id: UUID) -> list[dict]:
    """
    Gets a list of attendance records for an event.
    """
    if Registration is None:
        raise ImportError("Registration model not available")

    rows = db.execute(
        select(Attendance, Registration)
        .join(Registration, Registration.id == Attendance.registration_id)
        .where(Attendance.event_id == event_id)
        .order_by(Attendance.created_at)
    )

    result: list[dict] = []

    def _get_names(reg: _Registration) -> list[str]:
        return [
            n for n in (reg.p1_name, reg.p2_name, reg.p3_name, reg.p4_name)
            if n is not None
        ]

    for row in rows:
        attendance = row[0]
        registration = row[1]
        names = _get_names(registration)

        result.append({
            "registration_id": str(attendance.registration_id),
            "ticket_code": getattr(registration, "ticket_code", None) or "",
            "participant_name": registration.p1_name or (names[0] if names else ""),
            "participant_names": names,
            "event_id": str(attendance.event_id),
            "status": attendance.status.value,
            "method": attendance.method.value if attendance.method is not None else None,
            "checked_in_at": attendance.checked_in_at.isoformat() if attendance.checked_in_at is not None else None,
            "checked_in_by": str(attendance.checked_in_by) if attendance.checked_in_by is not None else None,
            "team_name": registration.team_name or "",
        })

    return result
