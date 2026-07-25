from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide one database session for an API request."""

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()