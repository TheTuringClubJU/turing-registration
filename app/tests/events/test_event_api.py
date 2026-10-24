from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import _create_token
from app.events.policy import registration_is_open
from app.tests.test_schema_constraints import make_event


def payload(**changes):
    data = dict(slug="test-workshop", name="Test workshop", type="workshop",
                min_team_size=1, max_team_size=1, is_active=True,
                reg_open_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
    data.update(changes)
    return data


def test_empty_and_missing_events(client):
    assert client.get("/events/active").status_code == 404
    assert client.get("/events/missing").status_code == 404


@pytest.mark.parametrize("size", [1, 4])
def test_create_and_read_contract(client, organiser, size):
    response = client.post("/events", json=payload(max_team_size=size),
                           headers={"Authorization": "Bearer " + _create_token(organiser.id)})
    assert response.status_code == 201, response.text
    event = response.json()
    assert event["code"].startswith(f"WORKSHOP-{datetime.now(timezone.utc).year}-")
    assert int(event["code"].rsplit("-", 1)[1]) >= 1
    assert event["reg_open"] is True
    assert event["max_team_size"] == size
    assert client.get("/events/active").json() == event
    assert client.get("/events/test-workshop").json() == event
    assert "event_code" not in event


def test_creation_requires_organiser(client):
    assert client.post("/events", json=payload()).status_code == 401


@pytest.mark.parametrize("changes", [
    {"min_team_size": 0}, {"max_team_size": 5}, {"min_team_size": 3, "max_team_size": 2},
    {"name": "  "}, {"slug": "Invalid Slug"}, {"slug": "active"}, {"type": "unknown"},
    {"reg_open_at": "2026-01-01T00:00:00"}, {"min_team_size": True},
    {"reg_open_at": "2026-01-02T00:00:00Z", "reg_close_at": "2026-01-01T00:00:00Z"},
])
def test_bad_event_returns_422(client, organiser, changes):
    response = client.post("/events", json=payload(**changes),
                           headers={"Authorization": "Bearer " + _create_token(organiser.id)})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][0] == "body"


def test_duplicate_slug_and_second_active_are_conflicts(client, organiser):
    headers = {"Authorization": "Bearer " + _create_token(organiser.id)}
    assert client.post("/events", json=payload(), headers=headers).status_code == 201
    assert client.post("/events", json=payload(is_active=False), headers=headers).status_code == 409
    assert client.post("/events", json=payload(slug="second"), headers=headers).status_code == 409
    assert client.get("/events/active").json()["slug"] == "test-workshop"
    assert client.post("/events", json=payload(slug="third", is_active=False), headers=headers).status_code == 201


@pytest.mark.parametrize("active,offset,close_offset,expected", [
    (True, 0, 1, True), (True, -1, 0, False), (True, 1, 2, False),
    (False, -1, 1, False), (True, -1, None, True), (True, -2, -1, False),
])
def test_open_window_boundaries(active, offset, close_offset, expected):
    now = datetime.now(timezone.utc)
    event = make_event(is_active=active, reg_open_at=now + timedelta(hours=offset),
                       reg_close_at=None if close_offset is None else now + timedelta(hours=close_offset))
    assert registration_is_open(event, now) is expected


def test_closed_event_lookup(client, db_session):
    event = make_event(is_active=True, reg_open_at=datetime.now(timezone.utc) + timedelta(hours=1))
    db_session.add(event)
    db_session.flush()
    assert client.get("/events/active").json()["reg_open"] is False

