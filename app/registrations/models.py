"""
app/registrations/models.py

SQLAlchemy model for the `registrations` table.
Must always mirror schema.sql exactly — schema.sql is the source of truth.

Note: duplicate-email prevention across p1-p4 for the same event_id, and
"exactly one is_lead = true", are NOT expressible as DB constraints across
four slot-pairs — those are enforced in app code (registrations/crud.py +
registrations/validators.py), not here.
"""

import uuid
import enum

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RegistrationStatus(str, enum.Enum):
    registered = "registered"
    cancelled = "cancelled"
    # 'attended' intentionally NOT added here — attendance state lives on
    # the separate `attendance` table, not on registration status.


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)

    team_name = Column(String(200), nullable=True)  # forced NULL server-side if max_team_size = 1

    # Slot 1 — team lead, or the solo registrant. Always required.
    p1_name = Column(String(200), nullable=False)
    p1_email = Column(String(320), nullable=False)
    p1_phone = Column(String(20), nullable=False)
    p1_is_lead = Column(Boolean, nullable=False, default=True)

    # Slots 2-4 — nullable, filled up to max_team_size, required up to min_team_size
    p2_name = Column(String(200), nullable=True)
    p2_email = Column(String(320), nullable=True)
    p2_phone = Column(String(20), nullable=True)
    p2_is_lead = Column(Boolean, nullable=False, default=False)

    p3_name = Column(String(200), nullable=True)
    p3_email = Column(String(320), nullable=True)
    p3_phone = Column(String(20), nullable=True)
    p3_is_lead = Column(Boolean, nullable=False, default=False)

    p4_name = Column(String(200), nullable=True)
    p4_email = Column(String(320), nullable=True)
    p4_phone = Column(String(20), nullable=True)
    p4_is_lead = Column(Boolean, nullable=False, default=False)

    status = Column(
        Enum(RegistrationStatus, name="registration_status"),
        nullable=False,
        default=RegistrationStatus.registered,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    event = relationship("Event", backref="registrations")

    __table_args__ = (
        Index("idx_registrations_event_id", "event_id"),
    )

    def participant_slots(self) -> list[dict]:
        """
        Helper: returns the filled p1-p4 slots as a list of dicts, skipping
        any slot whose name is None. Used by crud.py / validators.py instead
        of repeating p1/p2/p3/p4 attribute access everywhere.
        """
        slots = []
        for i in range(1, 5):
            name = getattr(self, f"p{i}_name")
            if name is None:
                continue
            slots.append(
                {
                    "slot": i,
                    "name": name,
                    "email": getattr(self, f"p{i}_email"),
                    "phone": getattr(self, f"p{i}_phone"),
                    "is_lead": getattr(self, f"p{i}_is_lead"),
                }
            )
        return slots

    def __repr__(self) -> str:
        return f"<Registration {self.id} event={self.event_id} team={self.team_name}>"