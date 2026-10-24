"""Tests for team_name rules across solo and team events."""
from types import SimpleNamespace

import pytest

from app.registrations.schemas import RegistrationCreate
from app.registrations.validators import RegistrationValidationError, validate_registration


def test_solo_event_forces_team_name_null_even_if_provided():
    rules = SimpleNamespace(min_team_size=1, max_team_size=1)
    payload = RegistrationCreate(
        team_name="My Solo Squad",
        participants=[
            {"name": "Solo", "email": "solo@example.com", "phone": "+919876543210", "is_team_lead": False}
        ],
    )
    result = validate_registration(payload, rules)
    assert result.team_name is None


@pytest.mark.parametrize("blank_name", [None, "", "   "])
def test_team_event_rejects_missing_or_blank_team_name(blank_name):
    rules = SimpleNamespace(min_team_size=2, max_team_size=4)
    payload = RegistrationCreate(
        team_name=blank_name,
        participants=[
            {"name": "Lead", "email": "lead@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Member", "email": "member@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    )
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(payload, rules)
    assert exc.value.errors[0]["loc"] == ["body", "team_name"]


def test_team_event_accepts_valid_team_name():
    rules = SimpleNamespace(min_team_size=2, max_team_size=4)
    payload = RegistrationCreate(
        team_name="Alpha Coders",
        participants=[
            {"name": "Lead", "email": "lead@example.com", "phone": "+919876543210", "is_team_lead": True},
            {"name": "Member", "email": "member@example.com", "phone": "+919876543211", "is_team_lead": False},
        ],
    )
    result = validate_registration(payload, rules)
    assert result.team_name == "Alpha Coders"
