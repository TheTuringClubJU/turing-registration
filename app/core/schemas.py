"""
app/core/schemas.py

Shared cross-domain Pydantic schemas, including authentication schemas.
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: Optional[str] = Field(None, description="Organiser email address")
    username: Optional[str] = Field(None, description="Username/email alias for compatibility")
    password: str = Field(..., description="Organiser plaintext password")

    @property
    def identifier(self) -> str:
        return self.email or self.username or ""


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Bearer JWT token")
    token_type: str = Field("bearer", description="Token type")
