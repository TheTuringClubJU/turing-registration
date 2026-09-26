"""
app/attendance/models.py

SQLAlchemy models for `organisers` and `attendance` tables.
Must always mirror schema.sql exactly — schema.sql is the source of truth.
"""

import uuid
import enum

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AttendanceStatus(str, enum.Enum):
    not_checked_in = "not_checked_in"
    checked_in = "checked_in"


class CheckinMethod(str, enum.Enum):
    qr = "qr"
    manual = "manual"


class Organiser(Base):
    __tablename__ = "organisers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Organiser {self.email}>"


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    registration_id = Column(
        UUID(as_uuid=True),
        ForeignKey("registrations.id"),
        unique=True,
        nullable=False,
    )
    # Denormalized from registrations.event_id — fixed at row creation time,
    # never re-derived. Exists purely for fast per-event dashboard queries
    # without joining through registrations every time.
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)

    status = Column(
        Enum(AttendanceStatus, name="attendance_status"),
        nullable=False,
        default=AttendanceStatus.not_checked_in,
    )
    method = Column(Enum(CheckinMethod, name="checkin_method"), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_by = Column(UUID(as_uuid=True), ForeignKey("organisers.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    registration = relationship("Registration", backref="attendance", uselist=False)
    event = relationship("Event")
    organiser = relationship("Organiser")

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