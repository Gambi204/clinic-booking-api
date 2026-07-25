import json
import logging
from datetime import UTC, datetime
from typing import Any


LOG_CONTEXT_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client",
)


class JsonFormatter(logging.Formatter):
    """Format application log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in LOG_CONTEXT_FIELDS:
            field_value = getattr(record, field_name, None)

            if field_value is not None:
                log_payload[field_name] = field_value

        if record.exc_info is not None:
            log_payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            log_payload,
            ensure_ascii=False,
            default=str,
        )


def configure_application_logger() -> logging.Logger:
    """Create the application logger without duplicating handlers."""

    application_logger = logging.getLogger("clinic_booking_api")

    if not application_logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(JsonFormatter())

        application_logger.addHandler(stream_handler)

    application_logger.setLevel(logging.INFO)
    application_logger.propagate = False

    return application_logger


logger = configure_application_logger()