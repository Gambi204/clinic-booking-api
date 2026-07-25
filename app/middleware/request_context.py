from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from app.core.logging import logger


REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128

CallNext = Callable[[Request], Awaitable[Response]]


def resolve_request_id(candidate: str | None) -> str:
    """Accept a reasonable client request ID or generate a new UUID."""

    if candidate is not None:
        normalized_candidate = candidate.strip()

        if (
            normalized_candidate
            and len(normalized_candidate)
            <= MAX_REQUEST_ID_LENGTH
        ):
            return normalized_candidate

    return str(uuid4())


async def add_request_context(
    request: Request,
    call_next: CallNext,
) -> Response:
    """Attach a request ID and log the completed HTTP request."""

    request_id = resolve_request_id(
        request.headers.get(REQUEST_ID_HEADER)
    )

    request.state.request_id = request_id

    started_at = perf_counter()

    client_address = (
        request.client.host
        if request.client is not None
        else None
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        logger.exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "client": client_address,
            },
        )

        raise

    duration_ms = round(
        (perf_counter() - started_at) * 1000,
        2,
    )

    response.headers[REQUEST_ID_HEADER] = request_id

    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client": client_address,
        },
    )

    return response