"""Pure validation: no database access and no changes to the caller's input."""
from typing import Protocol

from app.registrations.schemas import RegistrationCreate


class TeamRules(Protocol):
    min_team_size: int
    max_team_size: int


class RegistrationValidationError(ValueError):
    def __init__(self, errors: list[dict]):
        self.errors = errors
        super().__init__("Invalid registration")


def validate_registration(data: RegistrationCreate, event: TeamRules) -> RegistrationCreate:
    errors = []

    def error(field, message):
        errors.append({"loc": ["body", *field], "msg": message, "type": "value_error"})

    count = len(data.participants)
    if not event.min_team_size <= count <= event.max_team_size:
        error(["participants"], f"Expected {event.min_team_size} to {event.max_team_size} participants")
    if event.max_team_size > 1:
        if not data.team_name:
            error(["team_name"], "Team name is required for team events")
        if sum(p.is_team_lead for p in data.participants) != 1:
            error(["participants"], "Exactly one team lead is required")
    seen = set()
    for index, participant in enumerate(data.participants):
        if participant.email in seen:
            error(["participants", index, "email"], "Email occurs more than once in this submission")
        seen.add(participant.email)
    if errors:
        raise RegistrationValidationError(errors)
    result = data.model_copy(deep=True)
    if event.max_team_size == 1:
        result.team_name = None
        result.participants[0].is_team_lead = True
    return result
