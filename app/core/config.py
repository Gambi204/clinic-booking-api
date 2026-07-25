from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Clinic Booking API"
    app_version: str = "1.0.0"
    app_env: str = "development"

    database_url: str
    test_database_url: str | None = None

    clinic_timezone: str = "Africa/Nairobi"
    slot_duration_minutes: int = 30
    min_booking_notice_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    @field_validator(
        "database_url",
        "test_database_url",
        mode="before",
    )
    @classmethod
    def normalize_postgresql_driver(
        cls,
        value: object,
    ) -> object:
        """Use Psycopg 3 for generic PostgreSQL connection URLs."""

        if not isinstance(value, str):
            return value

        if value.startswith("postgresql://"):
            return value.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        if value.startswith("postgres://"):
            return value.replace(
                "postgres://",
                "postgresql+psycopg://",
                1,
            )

        return value


@lru_cache
def get_settings() -> Settings:
    """Create and cache one settings object for the application."""
    return Settings()


settings = get_settings()