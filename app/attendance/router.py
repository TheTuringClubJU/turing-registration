from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

# Import your QR generator function from qr.py
from app.attendance.qr import generate_image

router = APIRouter(prefix="", tags=["Attendance"])

# --- Pydantic Models for Request Validation ---
class ScanCheckInRequest(BaseModel):
    event_id: str
    registration_id: str

class ManualCheckInRequest(BaseModel):
    event_id: str
    registration_id: str
    notes: Optional[str] = None


# --- Dummy Auth Dependency Placeholder ---
async def verify_organiser_auth():
    """
    Placeholder for organiser authentication dependency.
    Replace this with your actual JWT/session auth check.
    """
    # Example: raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# --- Endpoints ---

@router.post("/attendance/scan")
async def scan_checkin(
    payload: ScanCheckInRequest,
    authorized: bool = Depends(verify_organiser_auth)
):
    """
    Organiser-auth required. Checks in an attendee via scanned QR method.
    """
    # TODO: Validate that registration_id exists in DB for event_id
    # TODO: Record check-in with method = "qr" in DB
    return {
        "status": "success",
        "message": "Checked in via QR successfully",
        "registration_id": payload.registration_id,
        "event_id": payload.event_id,
        "method": "qr"
    }


@router.post("/attendance/manual-checkin")
async def manual_checkin(
    payload: ManualCheckInRequest,
    authorized: bool = Depends(verify_organiser_auth)
):
    """
    Organiser-auth required. Checks in an attendee via manual method.
    """
    # TODO: Validate that registration_id exists in DB for event_id
    # TODO: Record check-in with method = "manual" in DB
    return {
        "status": "success",
        "message": "Checked in manually successfully",
        "registration_id": payload.registration_id,
        "event_id": payload.event_id,
        "method": "manual"
    }


@router.get("/attendance/summary")
async def get_attendance_summary(event_id: str):
    """
    Returns total check-ins, breakdown by method (qr vs manual), etc. for an event.
    """
    # TODO: Fetch summary from DB for event_id
    return {
        "event_id": event_id,
        "total_registered": 100,
        "total_checked_in": 45,
        "breakdown": {
            "qr": 40,
            "manual": 5
        }
    }


@router.get("/attendance/list")
async def get_attendance_list(event_id: str):
    """
    Returns the list of check-in records for a given event.
    """
    # TODO: Fetch attendee check-in list from DB for event_id
    return {
        "event_id": event_id,
        "attendees": [
            # Example record structure
            # {"registration_id": "...", "checked_in_at": "...", "method": "qr"}
        ]
    }


@router.get("/registrations/{id}/qr")
async def get_registration_qr(id: str):
    """
    Regenerates and returns the QR code PNG on demand.
    No auth required for now per open decisions.
    """
    # TODO (Optional): Verify if the registration ID actually exists in the DB 
    # before generating, to return a 404 if it doesn't exist.
    # if not db.registration_exists(id):
    #     raise HTTPException(status_code=404, detail="Registration not found")

    try:
        image_bytes = generate_image(id)
        
        # Return as an image response with media type PNG
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate QR code: {str(e)}"
        )