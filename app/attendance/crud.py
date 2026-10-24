from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.attendance.models import Attendance, AttendanceStatus, CheckinMethod

if TYPE_CHECKING:
    from app.registrations.models import Registration as _Registration

try:
    from app.registrations.models import Registration
except ImportError:
    Registration = None  # type: ignore[assignment,misc]

def mark_attended(db: Session, registration_id: UUID, method: CheckinMethod, organiser_id: UUID) -> Attendance:
    """
    Marks a specific registration as checked-in.
    
    Args:
        db: The SQLAlchemy session.
        registration_id: The ID of the registration to mark.
        method: The check-in method (qr or manual).
        organiser_id: The ID of the organiser performing the action.
        
    Returns:
        The updated Attendance object.
        
    Raises:
        LookupError: If the registration is not found.
        Exception: If database constraints are violated (e.g., already checked in, if logic changes).
    """
    # Fetch existing attendance record
    stmt = select(Attendance).where(Attendance.registration_id == registration_id)
    attendance = db.scalar(stmt)

    if attendance is None:
        raise LookupError("Registration not found")

    # Idempotency check: If already checked in, return as-is. 
    # The database constraint prevents "half-checked" states, so we don't need to validate method/time here strictly.
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
    Returns raw integers, not Pydantic models.
    """
    total_count = db.scalar(select(func.count(Attendance.id)).where(Attendance.event_id == event_id)) or 0
    
    checked_in_count = db.scalar(
        select(func.count(Attendance.id)).where(
            Attendance.event_id == event_id, 
            Attendance.status == AttendanceStatus.checked_in
        )
    ) or 0

    return {
        "total_registered": total_count,
        "checked_in": checked_in_count,
        "remaining": total_count - checked_in_count
    }


def get_list(db: Session, event_id: UUID) -> list[dict]:
    """
    Gets a list of attendance records for an event.
    Joins with Registration to get team details.
    Returns raw Python dicts ready for Pydantic serialization in the Router.
    """
    if Registration is None:
        raise ImportError("Registration model not available")

    # Execute query directly
    rows = db.execute(
        select(Attendance, Registration)
        .join(Registration, Registration.id == Attendance.registration_id)
        .where(Attendance.event_id == event_id)
        .order_by(Attendance.created_at)
    )

    result: list[dict] = []

    def _get_names(reg: _Registration) -> list[str]:
        """Extract non-null participant names from a registration row."""
        return [
            n for n in (reg.p1_name, reg.p2_name, reg.p3_name, reg.p4_name)
            if n is not None
        ]

    for row in rows:
        attendance = row[0]
        registration = row[1]

        # Construct the dict manually to avoid SQLAlchemy/Pydantic conflicts
        result.append({
            "registration_id": str(attendance.registration_id), # Serialize UUID to string immediately
            "event_id": str(attendance.event_id),               # Serialize UUID to string
            "status": attendance.status.value,                  # Extract enum value for JSON
            "method": attendance.method.value if attendance.method is not None else None,
            "checked_in_at": attendance.checked_in_at.isoformat() if attendance.checked_in_at is not None else None,
            "checked_in_by": str(attendance.checked_in_by) if attendance.checked_in_by is not None else None,
            "team_name": registration.team_name or "",          # Handle None team name gracefully
            "participant_names": _get_names(registration),
        })

    return result
