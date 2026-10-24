"""Tests for POST /events/{slug}/register HTTP contract and error codes."""
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from app.events.models import Event, EventType


def _make_active_event(db_session, **overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        event_code=f"API-{uuid.uuid4().hex[:8]}",
        slug=f"api-{uuid.uuid4().hex[:8]}",
        name="API Contract Event",
        type=EventType.workshop,
        min_team_size=1,
        max_team_size=1,
        is_active=True,
        reg_open_at=now,
    )
    defaults.update(overrides)
    event = Event(**defaults)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_register_returns_201_and_registration_out(client, db_session):
    event = _make_active_event(db_session)
    payload = {
        "participants": [
            {
                "name": "Solo Tester",
                "email": "solo@example.com",
                "phone": "+919876543210",
                "is_team_lead": True,
            }
        ]
    }

    response = client.post(f"/events/{event.slug}/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["status"] == "registered"
    assert "created_at" in data


def test_register_returns_201_for_team_payload(client, db_session):
    event = _make_active_event(db_session, min_team_size=2, max_team_size=4)
    payload = {
        "team_name": "Contract Team",
        "participants": [
            {"name": "Alice", "email": "alice-contract@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Bob", "email": "bob-contract@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    }
    response = client.post(f"/events/{event.slug}/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "registered"
    assert "created_at" in data


def test_register_returns_404_for_missing_event(client):

    payload = {
        "participants": [
            {"name": "Alice", "email": "alice@example.com", "phone": "+919876543210", "is_team_lead": True}
        ]
    }
    response = client.post("/events/non-existent-event-slug/register", json=payload)
    assert response.status_code == 404


def test_register_returns_409_for_closed_event(client, db_session):
    event = _make_active_event(db_session, is_active=False)
    payload = {
        "participants": [
            {"name": "Alice", "email": "alice@example.com", "phone": "+919876543210", "is_team_lead": True}
        ]
    }
    response = client.post(f"/events/{event.slug}/register", json=payload)
    assert response.status_code == 409


def test_register_returns_409_for_duplicate_submission(client, db_session):
    event = _make_active_event(db_session)
    payload = {
        "participants": [
            {"name": "Alice", "email": "alice@example.com", "phone": "+919876543210", "is_team_lead": True}
        ]
    }
    res1 = client.post(f"/events/{event.slug}/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post(f"/events/{event.slug}/register", json=payload)
    assert res2.status_code == 409


def test_register_returns_422_with_structured_field_errors(client, db_session):
    event = _make_active_event(db_session, min_team_size=2, max_team_size=2)
    # Missing team name for team event
    payload = {
        "team_name": None,
        "participants": [
            {"name": "Alice", "email": "alice@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Bob", "email": "bob@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    }
    response = client.post(f"/events/{event.slug}/register", json=payload)
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any(err.get("loc") == ["body", "team_name"] for err in errors)


def test_register_succeeds_even_if_qr_or_email_fails(client, db_session):
    event = _make_active_event(db_session)
    payload = {
        "participants": [
            {"name": "Alice", "email": "alice-resilient@example.com", "phone": "+919876543210", "is_team_lead": True}
        ]
    }

    # Simulate email/QR worker failure
    with patch("app.attendance.qr.generate_image", side_effect=RuntimeError("QR generation error"), create=True), \
            patch("app.email_templates.send.send_registration_confirmation", create=True):
        response = client.post(f"/events/{event.slug}/register", json=payload)
        # Background task failure must NOT undo the 201 response
        assert response.status_code == 201
