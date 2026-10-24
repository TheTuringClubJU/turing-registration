"""Tests for participant count validation across solo and team events."""
from types import SimpleNamespace

import pytest

from app.registrations.schemas import RegistrationCreate
from app.registrations.validators import RegistrationValidationError, validate_registration


def make_payload(count: int, **overrides):
    participants = [
        {
            "name": f"Person {i}",
            "email": f"p{i}@example.com",
            "phone": "+919876543210",
            "is_team_lead": (i == 1),
        }
        for i in range(1, count + 1)
    ]
    data = {
        "team_name": "Test Team" if count > 1 else None,
        "participants": participants,
    }
    data.update(overrides)
    return RegistrationCreate(**data)


def test_solo_event_accepts_exactly_one_participant():
    rules = SimpleNamespace(min_team_size=1, max_team_size=1)
    payload = make_payload(1)
    result = validate_registration(payload, rules)
    assert len(result.participants) == 1
    assert result.team_name is None
    assert result.participants[0].is_team_lead is True


@pytest.mark.parametrize("invalid_count", [2, 3, 4])
def test_solo_event_rejects_more_than_one(invalid_count):
    rules = SimpleNamespace(min_team_size=1, max_team_size=1)
    payload = make_payload(invalid_count)
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(payload, rules)
    assert exc.value.errors[0]["loc"] == ["body", "participants"]


@pytest.mark.parametrize("count", [2, 3, 4])
def test_team_event_accepts_valid_sizes(count):
    rules = SimpleNamespace(min_team_size=2, max_team_size=4)
    payload = make_payload(count)
    result = validate_registration(payload, rules)
    assert len(result.participants) == count


@pytest.mark.parametrize("count,min_size,max_size", [(1, 2, 4), (4, 2, 3), (1, 3, 4)])
def test_team_event_rejects_out_of_bounds(count, min_size, max_size):
    rules = SimpleNamespace(min_team_size=min_size, max_team_size=max_size)
    payload = make_payload(count)
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(payload, rules)
    assert exc.value.errors[0]["loc"] == ["body", "participants"]
