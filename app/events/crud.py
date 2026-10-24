"""Event operations. The creation function owns its transaction."""
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.events.models import Event
from app.events.schemas import EventCreate


def get_active_event(db: Session) -> Event | None:
    return db.scalar(select(Event).where(Event.is_active.is_(True)))


def get_event_by_slug(db: Session, slug: str) -> Event | None:
    return db.scalar(select(Event).where(Event.slug == slug))


def create_event(db: Session, data: EventCreate) -> Event:
    try:
        current_year = datetime.now(timezone.utc).year
        # Race-safe sequential event code allocation via schema.sql next_event_code()
        code = db.scalar(
            text("SELECT next_event_code(CAST(:type AS event_type), :year)"),
            {"type": data.type.value, "year": current_year},
        )
        event = Event(event_code=code, **data.model_dump())
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception:
        db.rollback()
        raise
