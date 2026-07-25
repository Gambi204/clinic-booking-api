from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    """An error that should be returned as a structured API response."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


async def api_error_handler(
    _request: Request,
    error: APIError,
) -> JSONResponse:
    """Convert an APIError into the standard error response."""

    error_content: dict[str, Any] = {
        "code": error.code,
        "message": error.message,
    }

    if error.details is not None:
        error_content["details"] = error.details

    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": error_content,
        },
    )