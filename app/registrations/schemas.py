"""Stable input/output contract for Vishad's registration endpoint."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Participant(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    email: EmailStr = Field(max_length=320)
    phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    is_team_lead: bool = Field(default=False, strict=True)

    @field_validator("email", mode="after")
    @classmethod
    def normalized_email(cls, value: str) -> str:
        return value.lower()


class RegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    team_name: str | None = Field(default=None, max_length=200)
    participants: list[Participant] = Field(min_length=1, max_length=4)


class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_code: str | None = None
    status: Literal["registered", "cancelled"]
    created_at: datetime
