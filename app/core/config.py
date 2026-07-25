from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Clinic Booking API"
    app_env: str = "development"
    database_url: str

    clinic_timezone: str = "Africa/Nairobi"
    slot_duration_minutes: int = 30
    min_booking_notice_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Create and cache one settings object for the application."""
    return Settings()


settings = get_settings()