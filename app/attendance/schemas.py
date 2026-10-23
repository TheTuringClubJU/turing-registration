from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CheckinRequest(BaseModel):
    registration_id: str = Field(..., description="The unique registration ID of the attendee")


class AttendanceOut(BaseModel):
    status: str = Field(..., description="Check-in status (e.g., 'success', 'already_checked_in')")
    method: str = Field(..., description="Check-in method used (e.g., 'qr', 'manual')")
    checked_in_at: datetime = Field(..., description="Timestamp when the check-in occurred")
    checked_in_by: Optional[str] = Field(None, description="Identifier of the organiser who performed the check-in")

    class Config:
        from_attributes = True


class SummaryOut(BaseModel):
    total_registered: int = Field(..., description="Total number of registrations for the event")
    checked_in: int = Field(..., description="Total number of attendees who have checked in")
    remaining: int = Field(..., description="Number of registered attendees yet to check in")

    class Config:
        from_attributes = True