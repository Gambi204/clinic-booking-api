from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Machine-readable and human-readable API error information."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Consistent response structure for handled API errors."""

    error: ErrorDetail