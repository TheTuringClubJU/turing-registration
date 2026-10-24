from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.events.models import Event, EventType
from app.events.policy import registration_is_open


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=200)
    type: EventType
    min_team_size: int = Field(ge=1, le=4, strict=True)
    max_team_size: int = Field(ge=1, le=4, strict=True)
    is_active: bool = False
    reg_open_at: AwareDatetime
    reg_close_at: AwareDatetime | None = None

    @field_validator("slug")
    @classmethod
    def reserved_slug(cls, value: str) -> str:
        if value == "active":
            raise ValueError("The slug active is reserved for the active-event endpoint")
        return value

    @model_validator(mode="after")
    def valid_ranges(self):
        if self.min_team_size > self.max_team_size:
            raise ValueError("min_team_size must not exceed max_team_size")
        if self.reg_close_at is not None and self.reg_close_at <= self.reg_open_at:
            raise ValueError("reg_close_at must be after reg_open_at")
        return self


class EventOut(BaseModel):
    id: UUID
    code: str
    slug: str
    name: str
    type: EventType
    min_team_size: int
    max_team_size: int
    is_active: bool
    reg_open: bool
    reg_open_at: datetime
    reg_close_at: datetime | None

    @classmethod
    def from_event(cls, event: Event):
        return cls(
            id=event.id, code=event.event_code, slug=event.slug, name=event.name,
            type=event.type, min_team_size=event.min_team_size, max_team_size=event.max_team_size,
            is_active=event.is_active, reg_open=registration_is_open(event),
            reg_open_at=event.reg_open_at, reg_close_at=event.reg_close_at,
        )
