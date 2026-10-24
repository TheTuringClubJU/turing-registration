"""
app/events/models.py

SQLAlchemy model for the `events` table.
Must always mirror schema.sql exactly — schema.sql is the source of truth.
"""

import uuid
import enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Enum,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class EventType(str, enum.Enum):
    workshop = "workshop"
    seminar = "seminar"
    hackathon = "hackathon"
    tech_event = "tech_event"
    other = "other"


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_code = Column(String(50), unique=True, nullable=False)  # e.g. WORKSHOP-2026-001
    slug = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(Enum(EventType, name="event_type"), nullable=False)

    min_team_size = Column(Integer, nullable=False)
    max_team_size = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=False)

    reg_open_at = Column(DateTime(timezone=True), nullable=False)
    reg_close_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("min_team_size >= 1", name="min_team_size_positive"),
        CheckConstraint("max_team_size >= 1", name="max_team_size_positive"),
        CheckConstraint("min_team_size <= max_team_size", name="min_le_max"),
        CheckConstraint(
            "reg_close_at IS NULL OR reg_close_at > reg_open_at",
            name="close_after_open",
        ),
        # Only one event can be active at a time — mirrors the partial unique
        # index in schema.sql (only_one_active_event). SQLAlchemy can declare
        # it here for documentation/Alembic purposes, but schema.sql's version
        # is what actually gets run.
        Index(
            "only_one_active_event",
            "is_active",
            unique=True,
            postgresql_where=(is_active == True),  # noqa: E712
        ),
    )

    def __repr__(self) -> str:
        return f"<Event {self.event_code} active={self.is_active}>"