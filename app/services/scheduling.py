from collections.abc import Iterable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.models import DoctorWorkingHours
from app.services.exceptions import AppointmentValidationError


def get_clinic_timezone(
    timezone_name: str | None = None,
) -> ZoneInfo:
    """Return the configured clinic timezone."""

    return ZoneInfo(timezone_name or settings.clinic_timezone)


def normalize_to_clinic_timezone(
    value: datetime,
    *,
    timezone_name: str | None = None,
    field_name: str = "start_at",
) -> datetime:
    """Convert an aware datetime into the clinic timezone."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise AppointmentValidationError(
            code="TIMEZONE_REQUIRED",
            message=(
                f"{field_name} must include a timezone offset, "
                "for example +03:00."
            ),
        )

    clinic_timezone = get_clinic_timezone(timezone_name)

    return value.astimezone(clinic_timezone)


def generate_slot_starts(
    service_date: date,
    working_periods: Iterable[DoctorWorkingHours],
    *,
    slot_duration_minutes: int | None = None,
    timezone_name: str | None = None,
) -> list[datetime]:
    """Generate all complete appointment start times for one date."""

    duration_minutes = (
        settings.slot_duration_minutes
        if slot_duration_minutes is None
        else slot_duration_minutes
    )

    if duration_minutes <= 0:
        raise ValueError("slot_duration_minutes must be greater than zero.")

    clinic_timezone = get_clinic_timezone(timezone_name)
    slot_duration = timedelta(minutes=duration_minutes)
    weekday = service_date.weekday()

    slot_starts: set[datetime] = set()

    relevant_periods = sorted(
        (
            period
            for period in working_periods
            if period.weekday == weekday
        ),
        key=lambda period: (period.start_time, period.end_time),
    )

    for period in relevant_periods:
        period_start = datetime.combine(
            service_date,
            period.start_time,
            tzinfo=clinic_timezone,
        )
        period_end = datetime.combine(
            service_date,
            period.end_time,
            tzinfo=clinic_timezone,
        )

        current_start = period_start

        while current_start + slot_duration <= period_end:
            slot_starts.add(current_start)
            current_start += slot_duration

    return sorted(slot_starts)


def validate_appointment_start(
    requested_start: datetime,
    working_periods: Iterable[DoctorWorkingHours],
    *,
    now: datetime | None = None,
    slot_duration_minutes: int | None = None,
    min_notice_minutes: int | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """Validate and normalize a proposed appointment start time."""

    clinic_timezone = get_clinic_timezone(timezone_name)

    normalized_start = normalize_to_clinic_timezone(
        requested_start,
        timezone_name=timezone_name,
        field_name="start_at",
    )

    current_time = (
        datetime.now(clinic_timezone)
        if now is None
        else normalize_to_clinic_timezone(
            now,
            timezone_name=timezone_name,
            field_name="now",
        )
    )

    if normalized_start <= current_time:
        raise AppointmentValidationError(
            code="APPOINTMENT_NOT_IN_FUTURE",
            message="The appointment start time must be in the future.",
        )

    notice_minutes = (
        settings.min_booking_notice_minutes
        if min_notice_minutes is None
        else min_notice_minutes
    )

    if notice_minutes < 0:
        raise ValueError("min_notice_minutes cannot be negative.")

    earliest_allowed_start = current_time + timedelta(
        minutes=notice_minutes,
    )

    if normalized_start < earliest_allowed_start:
        raise AppointmentValidationError(
            code="MINIMUM_NOTICE_NOT_MET",
            message=(
                f"Appointments must be booked at least "
                f"{notice_minutes} minutes in advance."
            ),
        )

    working_period_list = list(working_periods)

    periods_for_day = [
        period
        for period in working_period_list
        if period.weekday == normalized_start.date().weekday()
    ]

    if not periods_for_day:
        raise AppointmentValidationError(
            code="DOCTOR_NOT_WORKING",
            message="The doctor does not work on the requested date.",
        )

    valid_slot_starts = generate_slot_starts(
        normalized_start.date(),
        periods_for_day,
        slot_duration_minutes=slot_duration_minutes,
        timezone_name=timezone_name,
    )

    if normalized_start not in valid_slot_starts:
        raise AppointmentValidationError(
            code="INVALID_APPOINTMENT_SLOT",
            message=(
                "The requested time is not a valid 30-minute slot "
                "within the doctor's working hours."
            ),
        )

    return normalized_start


def get_available_slot_starts(
    service_date: date,
    working_periods: Iterable[DoctorWorkingHours],
    booked_starts: Iterable[datetime],
    *,
    now: datetime | None = None,
    slot_duration_minutes: int | None = None,
    min_notice_minutes: int | None = None,
    timezone_name: str | None = None,
) -> list[datetime]:
    """Return valid slots that are neither too soon nor already booked."""

    clinic_timezone = get_clinic_timezone(timezone_name)

    current_time = (
        datetime.now(clinic_timezone)
        if now is None
        else normalize_to_clinic_timezone(
            now,
            timezone_name=timezone_name,
            field_name="now",
        )
    )

    notice_minutes = (
        settings.min_booking_notice_minutes
        if min_notice_minutes is None
        else min_notice_minutes
    )

    if notice_minutes < 0:
        raise ValueError("min_notice_minutes cannot be negative.")

    earliest_allowed_start = current_time + timedelta(
        minutes=notice_minutes,
    )

    all_slot_starts = generate_slot_starts(
        service_date,
        working_periods,
        slot_duration_minutes=slot_duration_minutes,
        timezone_name=timezone_name,
    )

    normalized_booked_starts = {
        normalize_to_clinic_timezone(
            booked_start,
            timezone_name=timezone_name,
            field_name="booked_start",
        )
        for booked_start in booked_starts
    }

    return [
        slot_start
        for slot_start in all_slot_starts
        if slot_start >= earliest_allowed_start
        and slot_start not in normalized_booked_starts
    ]