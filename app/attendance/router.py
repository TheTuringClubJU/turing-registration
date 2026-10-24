"""
app/attendance/router.py

Attendance-domain HTTP routes.  All write routes require a valid
organiser JWT (require_valid_organiser dependency from core/security.py).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.attendance import crud, qr
from app.attendance.models import CheckinMethod, Organiser
from app.attendance.schemas import AttendanceOut, CheckinRequest, SummaryOut
from app.core.database import get_db
from app.core.security import require_valid_organiser

router = APIRouter(prefix="/attendance", tags=["attendance"])


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _checkin(
    registration_id: UUID,
    method: CheckinMethod,
    db: Session,
    organiser: Organiser,
) -> AttendanceOut:
    try:
        attendance = crud.mark_attended(db, registration_id, method, organiser.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return attendance


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/scan", response_model=AttendanceOut)
def scan(
    payload: CheckinRequest,
    db: Session = Depends(get_db),
    organiser: Organiser = Depends(require_valid_organiser),
):
    """QR scan check-in — method=qr."""
    return _checkin(payload.registration_id, CheckinMethod.qr, db, organiser)


@router.post("/manual-checkin", response_model=AttendanceOut)
def manual_checkin(
    payload: CheckinRequest,
    db: Session = Depends(get_db),
    organiser: Organiser = Depends(require_valid_organiser),
):
    """Manual check-in — method=manual."""
    return _checkin(payload.registration_id, CheckinMethod.manual, db, organiser)


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


@router.get("/registrations/{registration_id}/qr")
def registration_qr(registration_id: UUID):
    """
    Generate and return the QR code PNG for a registration on demand.
    No auth for now — registration_id is a UUID so it's hard to guess.
    """
    image_bytes = qr.generate_image(str(registration_id))
    return Response(content=image_bytes, media_type="image/png")
