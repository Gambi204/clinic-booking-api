from app.core.config import Settings


def test_render_postgresql_url_uses_psycopg_driver() -> None:
    config = Settings(
        database_url=(
            "postgresql://render_user:render_password"
            "@private-host:5432/clinic_booking_db"
        ),
        test_database_url=None,
        _env_file=None,
    )

    assert config.database_url == (
        "postgresql+psycopg://render_user:render_password"
        "@private-host:5432/clinic_booking_db"
    )


def test_existing_psycopg_url_remains_unchanged() -> None:
    database_url = (
        "postgresql+psycopg://clinic_app:password"
        "@localhost:5432/clinic_booking_db"
    )

    config = Settings(
        database_url=database_url,
        test_database_url=None,
        _env_file=None,
    )

    assert config.database_url == database_url


def test_legacy_postgres_scheme_is_normalized() -> None:
    config = Settings(
        database_url=(
            "postgres://legacy_user:legacy_password"
            "@legacy-host:5432/clinic_booking_db"
        ),
        test_database_url=None,
        _env_file=None,
    )

    assert config.database_url == (
        "postgresql+psycopg://legacy_user:legacy_password"
        "@legacy-host:5432/clinic_booking_db"
    )