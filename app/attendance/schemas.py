from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.attendance.models import AttendanceStatus, CheckinMethod


class CheckinRequest(BaseModel):
    registration_id: UUID = Field(..., description="The unique registration ID of the attendee")


class AttendanceOut(BaseModel):
    registration_id: UUID = Field(..., description="The registration this attendance record belongs to")
    status: AttendanceStatus = Field(..., description="Check-in status")
    method: Optional[CheckinMethod] = Field(None, description="Check-in method (qr or manual)")
    checked_in_at: Optional[datetime] = Field(None, description="Timestamp when the check-in occurred")
    checked_in_by: Optional[UUID] = Field(None, description="UUID of the organiser who performed the check-in")

    class Config:
        from_attributes = True


class SummaryOut(BaseModel):
    total_registered: int = Field(..., description="Total number of registrations for the event")
    checked_in: int = Field(..., description="Total number of attendees who have checked in")
    remaining: int = Field(..., description="Number of registered attendees yet to check in")

    class Config:
        from_attributes = True
