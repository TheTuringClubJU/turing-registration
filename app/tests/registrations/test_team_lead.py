"""Tests for team lead rules across solo and team events."""
from types import SimpleNamespace

import pytest

from app.registrations.schemas import RegistrationCreate
from app.registrations.validators import RegistrationValidationError, validate_registration


def test_solo_forces_lead_true_when_sent_false():
    rules = SimpleNamespace(min_team_size=1, max_team_size=1)
    payload = RegistrationCreate(
        participants=[
            {"name": "Solo", "email": "solo@example.com", "phone": "+919876543210", "is_team_lead": False}
        ]
    )
    result = validate_registration(payload, rules)
    assert result.participants[0].is_team_lead is True


@pytest.mark.parametrize("leads", [[False, False], [True, True], [False, False, False], [True, True, True]])
def test_team_event_rejects_zero_or_multiple_leads(leads):
    rules = SimpleNamespace(min_team_size=2, max_team_size=4)
    participants = [
        {"name": f"P{i}", "email": f"p{i}@example.com", "phone": "+919876543210", "is_team_lead": lead}
        for i, lead in enumerate(leads)
    ]
    payload = RegistrationCreate(team_name="Team Lead Test", participants=participants)
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(payload, rules)
    assert exc.value.errors[0]["loc"] == ["body", "participants"]


@pytest.mark.parametrize("lead_slot", [0, 1, 2, 3])
def test_team_lead_can_be_in_any_slot(lead_slot):
    rules = SimpleNamespace(min_team_size=4, max_team_size=4)
    participants = [
        {"name": f"P{i}", "email": f"p{i}@example.com", "phone": "+919876543210", "is_team_lead": (i == lead_slot)}
        for i in range(4)
    ]
    payload = RegistrationCreate(team_name="Team Lead Flex", participants=participants)
    result = validate_registration(payload, rules)
    assert result.participants[lead_slot].is_team_lead is True
    assert sum(p.is_team_lead for p in result.participants) == 1
