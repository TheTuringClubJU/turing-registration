"""
app/attendance/models.py

SQLAlchemy models for `organisers` and `attendance` tables.
Must always mirror schema.sql exactly — schema.sql is the source of truth.

Uses the modern Mapped / mapped_column API so Pylance resolves instance
attribute types correctly (avoids Column[X] vs X confusion).
"""

import uuid
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import (
    String,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttendanceStatus(str, enum.Enum):
    not_checked_in = "not_checked_in"
    checked_in = "checked_in"


class CheckinMethod(str, enum.Enum):
    qr = "qr"
    manual = "manual"


class Organiser(Base):
    __tablename__ = "organisers"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Organiser {self.username}>"


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    registration_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("registrations.id"),
        unique=True,
        nullable=False,
    )
    # Denormalized from registrations.event_id — fixed at row creation time,
    # never re-derived. Exists purely for fast per-event dashboard queries
    # without joining through registrations every time.
    event_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status"),
        nullable=False,
        default=AttendanceStatus.not_checked_in,
    )
    method: Mapped[Optional[CheckinMethod]] = mapped_column(
        Enum(CheckinMethod, name="checkin_method"), nullable=True
    )
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checked_in_by: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisers.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    registration: Mapped[Optional["Registration"]] = relationship(  # type: ignore[name-defined]
        "Registration", backref="attendance", uselist=False
    )
    event: Mapped[Optional["Event"]] = relationship("Event")  # type: ignore[name-defined]
    organiser: Mapped[Optional["Organiser"]] = relationship("Organiser")

    __table_args__ = (
        Index("idx_attendance_event_id", "event_id"),
        # Either all three check-in fields are set, or none are —
        # no half-checked-in rows.
        CheckConstraint(
            "(method IS NULL AND checked_in_at IS NULL AND checked_in_by IS NULL) "
            "OR (method IS NOT NULL AND checked_in_at IS NOT NULL AND checked_in_by IS NOT NULL)",
            name="checkin_fields_consistent",
        ),
    )

    def __repr__(self) -> str:
        return f"<Attendance reg={self.registration_id} status={self.status}>"
