from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.registrations.schemas import RegistrationCreate
from app.registrations.validators import RegistrationValidationError, validate_registration


def submission(count=1, **changes):
    data = {"team_name": "Team", "participants": [
        {"name": f"Person {i}", "email": f"person{i}@example.com", "phone": "+919876543210",
         "is_team_lead": i == 0} for i in range(count)]}
    data.update(changes)
    return data


def rules(minimum=1, maximum=1):
    return SimpleNamespace(min_team_size=minimum, max_team_size=maximum)


def test_solo_normalizes_without_mutating_input():
    source = submission()
    source["participants"][0]["is_team_lead"] = False
    data = RegistrationCreate(**source)
    normalized = validate_registration(data, rules())
    assert normalized.team_name is None
    assert normalized.participants[0].is_team_lead is True
    assert data.team_name == "Team"
    assert data.participants[0].is_team_lead is False


@pytest.mark.parametrize("count", [2, 3, 4])
def test_team_accepts_min_middle_max(count):
    assert len(validate_registration(RegistrationCreate(**submission(count)), rules(2, 4)).participants) == count


@pytest.mark.parametrize("count,minimum,maximum", [(1, 2, 4), (4, 2, 3), (2, 1, 1)])
def test_count_rejected(count, minimum, maximum):
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(RegistrationCreate(**submission(count)), rules(minimum, maximum))
    assert exc.value.errors[0]["loc"] == ["body", "participants"]


@pytest.mark.parametrize("name", [None, "", "   "])
def test_team_name_required(name):
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(RegistrationCreate(**submission(2, team_name=name)), rules(2, 4))
    assert exc.value.errors[0]["loc"] == ["body", "team_name"]


@pytest.mark.parametrize("leads", [[False, False], [True, True]])
def test_exactly_one_lead(leads):
    data = submission(2)
    for participant, lead in zip(data["participants"], leads):
        participant["is_team_lead"] = lead
    with pytest.raises(RegistrationValidationError):
        validate_registration(RegistrationCreate(**data), rules(2, 4))


def test_lead_can_be_any_slot():
    data = submission(2)
    data["participants"][0]["is_team_lead"] = False
    data["participants"][1]["is_team_lead"] = True
    assert validate_registration(RegistrationCreate(**data), rules(2, 4)).participants[1].is_team_lead


def test_duplicate_email_is_case_insensitive_and_field_specific():
    data = submission(2)
    data["participants"][1]["email"] = " PERSON0@EXAMPLE.COM "
    with pytest.raises(RegistrationValidationError) as exc:
        validate_registration(RegistrationCreate(**data), rules(2, 4))
    assert exc.value.errors[0]["loc"] == ["body", "participants", 1, "email"]


@pytest.mark.parametrize("field,value", [
    ("email", "wrong"), ("email", ""), ("phone", "123"), ("phone", "9876543210"),
    ("phone", "+0123456789"), ("phone", "+1234567890123456"), ("name", "   "),
    ("is_team_lead", "true"),
])
def test_contact_and_required_field_validation(field, value):
    data = submission()
    data["participants"][0][field] = value
    with pytest.raises(ValidationError) as exc:
        RegistrationCreate(**data)
    assert exc.value.errors()[0]["loc"] == ("participants", 0, field)


@pytest.mark.parametrize("count", [0, 5])
def test_global_slot_limits(count):
    with pytest.raises(ValidationError):
        RegistrationCreate(**submission(count))


def test_optional_slots_are_omitted_not_null():
    data = submission(2)
    assert len(validate_registration(RegistrationCreate(**data), rules(1, 4)).participants) == 2
    data["participants"].append(None)
    with pytest.raises(ValidationError):
        RegistrationCreate(**data)
