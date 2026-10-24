from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.attendance.models import AttendanceStatus, CheckinMethod


class CheckinRequest(BaseModel):
    registration_id: Optional[str] = Field(None, description="The unique registration ID or ticket code of the attendee")
    identifier: Optional[str] = Field(None, description="Alternative field for ticket code or registration ID")
    query: Optional[str] = Field(None, description="Alternative field for query/identifier")

    @property
    def target_query(self) -> str:
        return (self.query or self.registration_id or self.identifier or "").strip()


class AttendanceOut(BaseModel):
    registration_id: UUID = Field(..., description="The registration this attendance record belongs to")
    ticket_code: Optional[str] = Field(None, description="Short ticket code (e.g. TTC-7K9X)")
    participant_name: Optional[str] = Field(None, description="Primary attendee or team lead name")
    participant_names: Optional[list[str]] = Field(default_factory=list, description="All participant names in team/solo")
    team_name: Optional[str] = Field(None, description="Team name if applicable")
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
