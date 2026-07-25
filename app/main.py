from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.errors import (
    APIError,
    api_error_handler,
    request_validation_error_handler,
)
from app.api.router import api_router
from app.core.config import settings
from app.db.dependencies import get_db
from fastapi.exceptions import RequestValidationError
from app.middleware import add_request_context


app = FastAPI(
    title=settings.app_name,
    description=(
        "A REST API for managing doctor availability and "
        "patient appointments."
    ),
    version=settings.app_version,
)

app.middleware("http")(add_request_context)

app.add_exception_handler(
    APIError,
    api_error_handler,
)

app.add_exception_handler(
    RequestValidationError,
    request_validation_error_handler,
)

app.include_router(api_router)


@app.get("/", tags=["System"], summary="Display service information")
def root() -> dict[str, str]:
    """Return basic information about the API."""

    return {
        "name": settings.app_name,
        "status": "running",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"], summary="Check service health")
def health_check(
    database_session: Session = Depends(get_db),
) -> dict[str, str]:
    """Confirm that the API and PostgreSQL database are reachable."""

    try:
        database_session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        ) from error

    return {
        "status": "healthy",
        "service": "clinic-booking-api",
        "database": "reachable",
    }