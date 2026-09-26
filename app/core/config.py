"""
app/core/config.py

Reads environment variables into typed settings.
The ONLY place os.environ / .env values should be touched — every other
file imports `settings` from here rather than reading env vars directly.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    BREVO_API_KEY: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60 * 24  # organiser session length, default 24h

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()