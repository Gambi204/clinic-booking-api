from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
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


def get_request_id(request: Request) -> str | None:
    """Read the request ID assigned by the HTTP middleware."""

    return getattr(
        request.state,
        "request_id",
        None,
    )


async def api_error_handler(
    request: Request,
    error: APIError,
) -> JSONResponse:
    """Convert an APIError into the standard error response."""

    error_content: dict[str, Any] = {
        "code": error.code,
        "message": error.message,
    }

    request_id = get_request_id(request)

    if request_id is not None:
        error_content["request_id"] = request_id

    if error.details is not None:
        error_content["details"] = error.details

    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": error_content,
        },
    )


async def request_validation_error_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Return FastAPI request-validation failures consistently."""

    error_content: dict[str, Any] = {
        "code": "REQUEST_VALIDATION_ERROR",
        "message": "Request validation failed.",
        "details": {
            "errors": jsonable_encoder(error.errors()),
        },
    }

    request_id = get_request_id(request)

    if request_id is not None:
        error_content["request_id"] = request_id

    return JSONResponse(
        status_code=422,
        content={
            "error": error_content,
        },
    )