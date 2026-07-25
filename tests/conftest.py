from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app


if settings.test_database_url is None:
    raise RuntimeError(
        "TEST_DATABASE_URL must be configured before running tests."
    )

if "test" not in settings.test_database_url.lower():
    raise RuntimeError(
        "TEST_DATABASE_URL must point to a clearly named test database."
    )


test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> Generator[None, None, None]:
    """Create a clean schema once for the entire test session."""

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()

@pytest.fixture(scope="session")
def postgres_test_engine() -> Engine:
    """Expose the PostgreSQL engine to integration tests."""

    return test_engine


def clear_application_tables(engine: Engine) -> None:
    """Delete committed application data in foreign-key-safe order."""

    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def committed_database_session(
    postgres_test_engine: Engine,
) -> Generator[Session, None, None]:
    """
    Provide a normal committed session for concurrency tests.

    Unlike database_session, this fixture does not wrap the test in
    one outer transaction because concurrent connections must see
    committed setup records.
    """

    clear_application_tables(postgres_test_engine)

    session = Session(
        bind=postgres_test_engine,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        clear_application_tables(postgres_test_engine)

        
@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    """Provide an isolated database transaction for each test."""

    connection = test_engine.connect()
    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def client(
    database_session: Session,
) -> Generator[TestClient, None, None]:
    """Provide a FastAPI client connected to the test database."""

    def override_get_db() -> Generator[Session, None, None]:
        yield database_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()