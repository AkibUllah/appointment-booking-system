"""Application settings loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Appointment Booking API"
    database_url: str = "sqlite:///./booking.db"
    admin_token: str = "dev-admin-token"
    clinic_timezone: str = "Asia/Dhaka"

    cancel_min_hours_before: int = Field(default=2, ge=0)
    reschedule_min_hours_before: int = Field(default=2, ge=0)
    max_reschedules: int = Field(default=2, ge=0)
    booking_min_lead_minutes: int = Field(default=30, ge=0)
    booking_max_days_ahead: int = Field(default=30, ge=1)

    scheduler_enabled: bool = True
    reminder_interval_seconds: int = Field(default=60, ge=5)

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
