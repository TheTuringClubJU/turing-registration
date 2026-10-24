"""
app/core/schemas.py

Shared cross-domain Pydantic schemas, including authentication schemas.
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: Optional[str] = Field(None, description="Organiser username handle")
    email: Optional[str] = Field(None, description="Alias for username for backward compatibility")
    password: str = Field(..., description="Organiser plaintext password")

    @property
    def identifier(self) -> str:
        return self.username or self.email or ""


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Bearer JWT token")
    token_type: str = Field("bearer", description="Token type")
