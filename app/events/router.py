from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_valid_organiser
from app.events import crud
from app.events.schemas import EventCreate, EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/active", response_model=EventOut)
def active_event(db: Session = Depends(get_db)):
    event = crud.get_active_event(db)
    if event is None:
        raise HTTPException(404, "No active event")
    return EventOut.from_event(event)


@router.get("/{slug}", response_model=EventOut)
def event_by_slug(slug: str, db: Session = Depends(get_db)):
    event = crud.get_event_by_slug(db, slug)
    if event is None:
        raise HTTPException(404, "Event not found")
    return EventOut.from_event(event)


@router.post("", response_model=EventOut, status_code=201, dependencies=[Depends(require_valid_organiser)])
def new_event(data: EventCreate, db: Session = Depends(get_db)):
    try:
        return EventOut.from_event(crud.create_event(db, data))
    except IntegrityError:
        raise HTTPException(409, "Event slug/code already exists or another event is active") from None
