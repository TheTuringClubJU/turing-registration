"""
app/tests/events/test_event_config.py

Comprehensive tests for event configuration and creation contract:
- event code format
- sequential codes via next_event_code()
- concurrent creation race (threaded calls never return the same code)
- min <= max enforced
- max_team_size > 4 rejected
- only-one-active enforced
- active / slug lookups
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from app.core.security import _create_token
from app.events.crud import create_event
from app.events.models import Event, EventType
from app.events.schemas import EventCreate


def _event_payload(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "slug": f"config-{uuid4().hex[:8]}",
        "name": "Configuration Test Event",
        "type": "workshop",
        "min_team_size": 1,
        "max_team_size": 4,
        "is_active": False,
        "reg_open_at": (now - timedelta(hours=1)).isoformat(),
        "reg_close_at": (now + timedelta(days=2)).isoformat(),
    }
    data.update(overrides)
    return data


def test_event_code_format_and_sequential_generation(db_session):
    year = datetime.now(timezone.utc).year
    slug_prefix = f"seq-{uuid4().hex[:6]}"

    event1 = create_event(
        db_session,
        EventCreate(
            slug=f"{slug_prefix}-1",
            name="Seq 1",
            type=EventType.other,
            min_team_size=1,
            max_team_size=2,
            is_active=False,
            reg_open_at=datetime.now(timezone.utc),
        ),
    )
    event2 = create_event(
        db_session,
        EventCreate(
            slug=f"{slug_prefix}-2",
            name="Seq 2",
            type=EventType.other,
            min_team_size=1,
            max_team_size=2,
            is_active=False,
            reg_open_at=datetime.now(timezone.utc),
        ),
    )

    # Formats match OTHER-YYYY-XXX
    assert event1.event_code.startswith(f"OTHER-{year}-")
    assert event2.event_code.startswith(f"OTHER-{year}-")

    seq1 = int(event1.event_code.rsplit("-", 1)[1])
    seq2 = int(event2.event_code.rsplit("-", 1)[1])
    assert seq2 == seq1 + 1


def test_concurrent_creation_race_never_duplicates_code(test_engine):
    prefix = f"race-config-{uuid4().hex[:6]}"

    def _worker(index: int) -> str:
        with Session(test_engine) as session:
            ev = create_event(
                session,
                EventCreate(
                    slug=f"{prefix}-{index}",
                    name=f"Race {index}",
                    type=EventType.hackathon,
                    min_team_size=2,
                    max_team_size=4,
                    is_active=False,
                    reg_open_at=datetime.now(timezone.utc),
                ),
            )
            return ev.event_code

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            codes = list(executor.map(_worker, range(4)))

        # Every code must be completely unique
        assert len(set(codes)) == 4
        seqs = sorted(int(c.rsplit("-", 1)[1]) for c in codes)
        # Codes are strictly consecutive numbers
        assert seqs == list(range(seqs[0], seqs[0] + 4))
    finally:
        with test_engine.begin() as conn:
            conn.execute(delete(Event).where(Event.slug.startswith(prefix)))
            # Only the isolated CI database runs this committed concurrency test.
            conn.execute(text("DELETE FROM event_counters WHERE type = :type AND year = :year"),
                         {"type": "hackathon", "year": datetime.now(timezone.utc).year})


def test_min_le_max_enforced_in_schema():
    with pytest.raises(Exception):
        EventCreate(
            slug="invalid-range",
            name="Invalid Range Event",
            type=EventType.workshop,
            min_team_size=3,
            max_team_size=2,
            reg_open_at=datetime.now(timezone.utc),
        )


def test_max_team_size_greater_than_four_rejected_in_schema():
    with pytest.raises(Exception):
        EventCreate(
            slug="oversized-team",
            name="Oversized Team Event",
            type=EventType.workshop,
            min_team_size=1,
            max_team_size=5,
            reg_open_at=datetime.now(timezone.utc),
        )

def test_only_one_active_event_enforced(client, organiser, db_session):
    db_session.execute(text("UPDATE events SET is_active = FALSE WHERE is_active = TRUE"))
    db_session.commit()
    headers = {"Authorization": f"Bearer {_create_token(organiser.id)}"}
    p1 = _event_payload(slug=f"active-1-{uuid4().hex[:6]}", is_active=True)
    res1 = client.post("/events", json=p1, headers=headers)
    assert res1.status_code == 201

    p2 = _event_payload(slug=f"active-2-{uuid4().hex[:6]}", is_active=True)
    res2 = client.post("/events", json=p2, headers=headers)
    assert res2.status_code == 409


def test_active_and_slug_lookups(client, organiser, db_session):
    db_session.execute(text("UPDATE events SET is_active = FALSE WHERE is_active = TRUE"))
    db_session.commit()
    headers = {"Authorization": f"Bearer {_create_token(organiser.id)}"}
    target_slug = f"lookup-{uuid4().hex[:6]}"
    payload = _event_payload(slug=target_slug, name="Lookup Event", is_active=True)

    create_res = client.post("/events", json=payload, headers=headers)
    assert create_res.status_code == 201

    # Active lookup
    active_res = client.get("/events/active")
    assert active_res.status_code == 200
    assert active_res.json()["slug"] == target_slug

    # Slug lookup
    slug_res = client.get(f"/events/{target_slug}")
    assert slug_res.status_code == 200
    assert slug_res.json()["name"] == "Lookup Event"

    # Missing slug lookup -> 404
    missing_res = client.get(f"/events/non-existent-{uuid4().hex[:6]}")
    assert missing_res.status_code == 404
