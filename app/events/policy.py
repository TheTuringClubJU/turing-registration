"""Shared opening policy for event display and Vishad's registration route."""
from datetime import datetime, timezone
from typing import Protocol


class EventWindow(Protocol):
    is_active: bool
    reg_open_at: datetime
    reg_close_at: datetime | None


def registration_is_open(event: EventWindow, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return bool(event.is_active and event.reg_open_at <= now
                and (event.reg_close_at is None or now < event.reg_close_at))
