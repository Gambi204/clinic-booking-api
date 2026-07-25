from datetime import datetime

from app.services.scheduling import get_clinic_timezone


def get_current_time() -> datetime:
    """Return the current time in the configured clinic timezone."""

    return datetime.now(get_clinic_timezone())