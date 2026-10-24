"""Committed multi-connection checks, restricted to the isolated CI database."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.attendance.models import Attendance
from app.events.models import Event, EventType
from app.registrations.crud import DuplicateEmailError, create_registration
from app.registrations.models import Registration
from app.registrations.schemas import RegistrationCreate


def test_concurrent_duplicate_creates_only_one_registration_and_attendance(test_engine):
    slug = "duplicate-race-" + uuid4().hex
    with Session(test_engine) as session:
        event = Event(event_code=slug, slug=slug, name="Concurrent registration",
                      type=EventType.workshop, min_team_size=1, max_team_size=1,
                      is_active=True, reg_open_at=datetime.now(timezone.utc) - timedelta(hours=1))
        session.add(event)
        session.commit()
        event_id = event.id
    barrier = Barrier(2)

    def register(_):
        data = RegistrationCreate(participants=[{
            "name": "Concurrent Person", "email": "race@example.com", "phone": "+919876543210"
        }])
        with Session(test_engine) as session:
            barrier.wait(timeout=15)
            try:
                create_registration(session, slug, data)
                return "created"
            except DuplicateEmailError:
                return "duplicate"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(register, range(2))) == ["created", "duplicate"]
        with Session(test_engine) as session:
            assert session.scalar(select(func.count()).select_from(Registration).where(Registration.event_id == event_id)) == 1
            assert session.scalar(select(func.count()).select_from(Attendance).where(Attendance.event_id == event_id)) == 1
    finally:
        with test_engine.begin() as connection:
            connection.execute(delete(Attendance).where(Attendance.event_id == event_id))
            connection.execute(delete(Registration).where(Registration.event_id == event_id))
            connection.execute(delete(Event).where(Event.id == event_id))
