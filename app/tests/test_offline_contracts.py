"""Contract regression checks with explicit mocks; no claims about real SQL I/O."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.attendance import qr
from app.email_templates import send
from app.events.crud import create_event
from app.events.schemas import EventCreate
from app.registrations import crud
from app.registrations.router import _send_confirmation_background
from app.registrations.schemas import RegistrationCreate


def payload():
    return {"participants": [{"name": "Test Registrant", "email": "person@example.com",
                               "phone": "+919876543210", "is_team_lead": True}]}


def test_event_code_sql_binds_both_parameters():
    db = Mock()
    db.scalar.return_value = "TECH_EVENT_TEST"
    create_event(db, EventCreate(slug="binding-test", name="Test", type="tech_event",
                                min_team_size=1, max_team_size=1,
                                reg_open_at=datetime.now(timezone.utc)))
    statement, values = db.scalar.call_args.args[0], db.scalar.call_args.args[1]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert set(compiled.params) == {"type", "year"}
    assert values["type"] == "tech_event"
    assert "CAST(" in str(compiled)
    db.commit.assert_called_once()


@pytest.mark.parametrize("error,status", [(crud.EventNotFoundError("Missing"), 404),
                                           (crud.EventClosedError("Closed"), 409),
                                           (crud.DuplicateEmailError("Duplicate"), 409)])
def test_route_maps_crud_errors(offline_client, monkeypatch, error, status):
    monkeypatch.setattr(crud, "create_registration", Mock(side_effect=error))
    assert offline_client.post("/events/example/register", json=payload()).status_code == status


def test_route_input_errors_include_field_locations(offline_client):
    body = payload()
    body["participants"][0]["email"] = "bad-email"
    response = offline_client.post("/events/example/register", json=body)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "participants", 0, "email"]


@pytest.mark.parametrize("failure", [None, "qr", "email"])
def test_success_and_provider_failures_preserve_201(offline_client, monkeypatch, failure):
    identifier = uuid4()
    registration = SimpleNamespace(id=identifier, team_name=None, status="registered",
                                   created_at=datetime.now(timezone.utc))
    event = SimpleNamespace(name="Example", slug="example", event_code="EXAMPLE-001")
    monkeypatch.setattr(crud, "create_registration", Mock(return_value=(
        registration, event, RegistrationCreate(**payload()))))
    generate = Mock(return_value=b"mock-image", side_effect=RuntimeError("private details") if failure == "qr" else None)
    deliver = Mock(side_effect=RuntimeError("private details") if failure == "email" else None)
    monkeypatch.setattr(qr, "generate_image", generate, raising=False)
    monkeypatch.setattr(send, "send_registration_confirmation", deliver, raising=False)
    response = offline_client.post("/events/example/register", json=payload())
    assert response.status_code == 201
    assert response.json()["id"] == str(identifier)
    generate.assert_called_once_with(str(identifier))
    if failure != "qr":
        assert deliver.call_args.kwargs["registration_id"] == str(identifier)
        assert deliver.call_args.kwargs["qr_bytes"] == b"mock-image"


def test_missing_owner_providers_are_reported_as_pending(caplog):
    _send_confirmation_background("test@example.com", {"name": "Test"}, None, [], str(uuid4()))
    assert "Confirmation pending" in caplog.text
    assert "test@example.com" not in caplog.text


@pytest.mark.parametrize("slot", [1, 2, 3, 4])
def test_duplicate_check_normalizes_stored_emails_in_each_slot(slot):
    db = Mock()
    db.scalar.return_value = SimpleNamespace(id=uuid4(), min_team_size=1, max_team_size=1,
                                           is_active=True, reg_open_at=datetime.now(timezone.utc), reg_close_at=None)
    stored = Mock()
    stored.participant_slots.return_value = [{"slot": slot, "email": " PERSON@EXAMPLE.COM "}]
    db.scalars.return_value.all.return_value = [stored]
    with pytest.raises(crud.DuplicateEmailError):
        crud.create_registration(db, "example", RegistrationCreate(**payload()))
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
