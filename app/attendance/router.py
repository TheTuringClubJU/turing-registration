"""
app/attendance/router.py

Attendance-domain HTTP routes.  All write routes require a valid
organiser JWT (require_valid_organiser dependency from core/security.py).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.attendance import crud, qr
from app.attendance.models import CheckinMethod, Organiser
from app.attendance.schemas import AttendanceOut, CheckinRequest, SummaryOut
from app.core.database import get_db
from app.core.security import require_valid_organiser
from app.events.models import Event
from app.registrations.models import Registration

router = APIRouter(prefix="/attendance", tags=["attendance"])


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _checkin(
    identifier: str,
    method: CheckinMethod,
    db: Session,
    organiser: Organiser,
) -> AttendanceOut:
    try:
        attendance = crud.mark_attended(db, identifier, method, organiser.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Enrich with participant & team name for the response display
    reg = db.scalar(select(Registration).where(Registration.id == attendance.registration_id))

    return AttendanceOut(
        registration_id=attendance.registration_id,
        ticket_code=getattr(reg, "ticket_code", None) if reg else None,
        participant_name=getattr(reg, "p1_name", "") if reg else "",
        team_name=getattr(reg, "team_name", None) if reg else None,
        status=attendance.status,
        method=attendance.method,
        checked_in_at=attendance.checked_in_at,
        checked_in_by=attendance.checked_in_by,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/scan", response_model=AttendanceOut)
def scan(
    payload: CheckinRequest,
    db: Session = Depends(get_db),
    organiser: Organiser = Depends(require_valid_organiser),
):
    """QR scan check-in — accepts raw UUID or ticket_code."""
    return _checkin(payload.target_query, CheckinMethod.qr, db, organiser)


@router.post("/manual-checkin", response_model=AttendanceOut)
def manual_checkin(
    payload: CheckinRequest,
    db: Session = Depends(get_db),
    organiser: Organiser = Depends(require_valid_organiser),
):
    """Manual check-in — accepts short ticket_code (e.g. TTC-7K9X) or raw UUID."""
    return _checkin(payload.target_query, CheckinMethod.manual, db, organiser)


@router.get("/summary", response_model=SummaryOut)
def summary(
    event_id: UUID,
    db: Session = Depends(get_db),
    _: Organiser = Depends(require_valid_organiser),
):
    """Aggregate counts for the dashboard (total / checked-in / remaining)."""
    return crud.get_summary(db, event_id)


@router.get("/list", response_model=list[AttendanceOut])
def attendance_list(
    event_id: UUID,
    db: Session = Depends(get_db),
    _: Organiser = Depends(require_valid_organiser),
):
    """All attendance records for one event — used by the dashboard table."""
    return crud.get_list(db, event_id)


@router.get("/active-event")
def get_active_event(
    db: Session = Depends(get_db),
    _: Organiser = Depends(require_valid_organiser),
):
    """Returns the currently active event in the database."""
    ev = db.scalar(select(Event).where(Event.is_active == True))
    if ev is None:
        raise HTTPException(status_code=404, detail="No active event found")
    return {
        "id": str(ev.id),
        "name": ev.name,
        "event_code": ev.event_code,
        "type": ev.type.value if hasattr(ev.type, "value") else str(ev.type),
    }


@router.get("/registrations/{registration_id}/qr")
def registration_qr(registration_id: UUID):
    """
    Generate and return the QR code PNG for a registration on demand.
    No auth for now — registration_id is a UUID so it's hard to guess.
    """
    image_bytes = qr.generate_image(str(registration_id))
    return Response(content=image_bytes, media_type="image/png")
