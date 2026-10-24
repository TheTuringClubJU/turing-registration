"""
app/events/models.py

SQLAlchemy model for the `events` table.
Must always mirror schema.sql exactly — schema.sql is the source of truth.

Uses Mapped / mapped_column so Pylance resolves instance attribute types
correctly (avoids Column[X] vs X confusion).
"""

import uuid
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import (
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
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventType(str, enum.Enum):
    workshop = "workshop"
    seminar = "seminar"
    hackathon = "hackathon"
    tech_event = "tech_event"
    other = "other"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. WORKSHOP-2026-001
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type"), nullable=False)

    min_team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    max_team_size: Mapped[int] = mapped_column(Integer, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    reg_open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reg_close_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
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
            postgresql_where="is_active = TRUE",  # noqa: E712
        ),
    )

    def __repr__(self) -> str:
        return f"<Event {self.event_code} active={self.is_active}>"