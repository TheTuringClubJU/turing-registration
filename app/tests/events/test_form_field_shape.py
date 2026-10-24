"""
app/tests/events/test_form_field_shape.py

Tests for event API response shape and form field configuration:
- Response includes min/max team size, slug, code, name, type, reg_open bool
- Solo vs team ranges are correct for frontend dynamic form rendering
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text

from app.core.security import _create_token


def _make_payload(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "slug": f"shape-{uuid4().hex[:8]}",
        "name": "Shape Test Event",
        "type": "workshop",
        "min_team_size": 1,
        "max_team_size": 1,
        "is_active": True,
        "reg_open_at": (now - timedelta(hours=1)).isoformat(),
        "reg_close_at": (now + timedelta(days=2)).isoformat(),
    }
    data.update(overrides)
    return data


def test_solo_event_form_field_shape(client, organiser, db_session):
    db_session.execute(text("UPDATE events SET is_active = FALSE WHERE is_active = TRUE"))
    db_session.commit()
    headers = {"Authorization": f"Bearer {_create_token(organiser.id)}"}
    payload = _make_payload(min_team_size=1, max_team_size=1)
    res = client.post("/events", json=payload, headers=headers)
    assert res.status_code == 201


    event_data = res.json()
    # Contract shape verification
    required_keys = {"id", "code", "slug", "name", "type", "min_team_size", "max_team_size", "reg_open", "is_active", "reg_open_at", "reg_close_at"}
    assert required_keys.issubset(set(event_data.keys()))

    # Solo configuration
    assert event_data["min_team_size"] == 1
    assert event_data["max_team_size"] == 1
    assert event_data["reg_open"] is True

    # Active lookup returns exact same shape
    active_res = client.get("/events/active")
    assert active_res.status_code == 200
    assert active_res.json()["min_team_size"] == 1
    assert active_res.json()["max_team_size"] == 1


def test_team_event_form_field_shape(client, organiser):
    headers = {"Authorization": f"Bearer {_create_token(organiser.id)}"}
    # Deactivate existing active event by posting inactive or looking up
    payload = _make_payload(
        slug=f"team-shape-{uuid4().hex[:8]}",
        name="Team Shape Hackathon",
        type="hackathon",
        min_team_size=2,
        max_team_size=4,
        is_active=False,
    )
    res = client.post("/events", json=payload, headers=headers)
    assert res.status_code == 201

    event_data = res.json()
    # Team configuration
    assert event_data["min_team_size"] == 2
    assert event_data["max_team_size"] == 4
    assert event_data["type"] == "hackathon"

    # Slug lookup returns exact same shape
    slug_res = client.get(f"/events/{payload['slug']}")
    assert slug_res.status_code == 200
    fetched = slug_res.json()
    assert fetched["min_team_size"] == 2
    assert fetched["max_team_size"] == 4
