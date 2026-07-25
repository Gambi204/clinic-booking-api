import json
import logging
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter


def test_generated_request_id_is_returned(
    client: TestClient,
) -> None:
    response = client.get("/")

    assert response.status_code == 200

    returned_request_id = response.headers["X-Request-ID"]

    UUID(returned_request_id)


def test_client_request_id_is_preserved(
    client: TestClient,
) -> None:
    supplied_request_id = "frontend-request-12345"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": supplied_request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == supplied_request_id


def test_empty_request_id_is_replaced(
    client: TestClient,
) -> None:
    response = client.get(
        "/",
        headers={
            "X-Request-ID": "   ",
        },
    )

    assert response.status_code == 200

    returned_request_id = response.headers["X-Request-ID"]

    assert returned_request_id.strip()
    UUID(returned_request_id)


def test_excessively_long_request_id_is_replaced(
    client: TestClient,
) -> None:
    supplied_request_id = "x" * 129

    response = client.get(
        "/",
        headers={
            "X-Request-ID": supplied_request_id,
        },
    )

    assert response.status_code == 200

    returned_request_id = response.headers["X-Request-ID"]

    assert returned_request_id != supplied_request_id
    UUID(returned_request_id)


def test_domain_error_contains_request_id(
    client: TestClient,
) -> None:
    supplied_request_id = "patient-request-404"

    response = client.get(
        "/patients/999/appointments",
        headers={
            "X-Request-ID": supplied_request_id,
        },
    )

    assert response.status_code == 404

    response_body = response.json()

    assert response_body["error"]["code"] == "PATIENT_NOT_FOUND"
    assert response_body["error"]["request_id"] == (
        supplied_request_id
    )

    assert response.headers["X-Request-ID"] == supplied_request_id


def test_validation_error_uses_structured_format(
    client: TestClient,
) -> None:
    supplied_request_id = "invalid-booking-request"

    response = client.post(
        "/appointments",
        json={},
        headers={
            "X-Request-ID": supplied_request_id,
        },
    )

    assert response.status_code == 422

    response_body = response.json()

    assert response_body["error"]["code"] == (
        "REQUEST_VALIDATION_ERROR"
    )

    assert response_body["error"]["message"] == (
        "Request validation failed."
    )

    assert response_body["error"]["request_id"] == (
        supplied_request_id
    )

    validation_errors = (
        response_body["error"]["details"]["errors"]
    )

    missing_fields = {
        error["loc"][-1]
        for error in validation_errors
    }

    assert {
        "doctor_id",
        "patient_id",
        "start_at",
    }.issubset(missing_fields)


def test_json_formatter_includes_request_context() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="clinic_booking_api",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )

    record.request_id = "formatter-test-id"
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.duration_ms = 4.75
    record.client = "127.0.0.1"

    formatted_log = json.loads(
        formatter.format(record)
    )

    assert formatted_log["level"] == "INFO"
    assert formatted_log["message"] == "request_completed"
    assert formatted_log["request_id"] == "formatter-test-id"
    assert formatted_log["method"] == "GET"
    assert formatted_log["path"] == "/health"
    assert formatted_log["status_code"] == 200
    assert formatted_log["duration_ms"] == 4.75
    assert formatted_log["client"] == "127.0.0.1"
    assert "timestamp" in formatted_log