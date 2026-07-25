from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models import DoctorWorkingHours
from app.services import (
    AppointmentValidationError,
    generate_slot_starts,
    get_available_slot_starts,
    normalize_to_clinic_timezone,
    validate_appointment_start,
)


NAIROBI = ZoneInfo("Africa/Nairobi")
MONDAY = date(2026, 7, 27)
TUESDAY = date(2026, 7, 28)


def working_period(
    weekday: int,
    start_value: str,
    end_value: str,
) -> DoctorWorkingHours:
    """Create an unsaved working-period object for service tests."""

    return DoctorWorkingHours(
        weekday=weekday,
        start_time=time.fromisoformat(start_value),
        end_time=time.fromisoformat(end_value),
    )


def test_generate_standard_thirty_minute_slots() -> None:
    periods = [
        working_period(0, "08:00", "10:00"),
    ]

    slots = generate_slot_starts(MONDAY, periods)

    assert [slot.time() for slot in slots] == [
        time(8, 0),
        time(8, 30),
        time(9, 0),
        time(9, 30),
    ]


def test_slots_are_aligned_to_working_period_start() -> None:
    periods = [
        working_period(0, "08:15", "10:15"),
    ]

    slots = generate_slot_starts(MONDAY, periods)

    assert [slot.time() for slot in slots] == [
        time(8, 15),
        time(8, 45),
        time(9, 15),
        time(9, 45),
    ]


def test_multiple_daily_periods_support_a_break() -> None:
    periods = [
        working_period(0, "08:00", "10:00"),
        working_period(0, "13:00", "14:00"),
    ]

    slots = generate_slot_starts(MONDAY, periods)

    assert [slot.time() for slot in slots] == [
        time(8, 0),
        time(8, 30),
        time(9, 0),
        time(9, 30),
        time(13, 0),
        time(13, 30),
    ]


def test_incomplete_final_slot_is_excluded() -> None:
    periods = [
        working_period(0, "08:00", "09:10"),
    ]

    slots = generate_slot_starts(MONDAY, periods)

    assert [slot.time() for slot in slots] == [
        time(8, 0),
        time(8, 30),
    ]


def test_overlapping_periods_do_not_duplicate_slots() -> None:
    periods = [
        working_period(0, "08:00", "10:00"),
        working_period(0, "08:30", "09:30"),
    ]

    slots = generate_slot_starts(MONDAY, periods)

    assert [slot.time() for slot in slots] == [
        time(8, 0),
        time(8, 30),
        time(9, 0),
        time(9, 30),
    ]


def test_naive_datetime_is_rejected() -> None:
    naive_start = datetime(2026, 7, 27, 10, 0)

    with pytest.raises(AppointmentValidationError) as error:
        normalize_to_clinic_timezone(naive_start)

    assert error.value.code == "TIMEZONE_REQUIRED"


def test_past_appointment_is_rejected() -> None:
    periods = [
        working_period(0, "08:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        10,
        0,
        tzinfo=NAIROBI,
    )

    requested_start = datetime(
        2026,
        7,
        27,
        9,
        30,
        tzinfo=NAIROBI,
    )

    with pytest.raises(AppointmentValidationError) as error:
        validate_appointment_start(
            requested_start,
            periods,
            now=current_time,
        )

    assert error.value.code == "APPOINTMENT_NOT_IN_FUTURE"


def test_appointment_within_notice_period_is_rejected() -> None:
    periods = [
        working_period(0, "08:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        8,
        0,
        tzinfo=NAIROBI,
    )

    requested_start = datetime(
        2026,
        7,
        27,
        8,
        30,
        tzinfo=NAIROBI,
    )

    with pytest.raises(AppointmentValidationError) as error:
        validate_appointment_start(
            requested_start,
            periods,
            now=current_time,
        )

    assert error.value.code == "MINIMUM_NOTICE_NOT_MET"


def test_exact_notice_boundary_is_allowed() -> None:
    periods = [
        working_period(0, "08:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        8,
        0,
        tzinfo=NAIROBI,
    )

    requested_start = datetime(
        2026,
        7,
        27,
        9,
        0,
        tzinfo=NAIROBI,
    )

    normalized_start = validate_appointment_start(
        requested_start,
        periods,
        now=current_time,
    )

    assert normalized_start == requested_start


def test_non_working_day_is_rejected() -> None:
    periods = [
        working_period(0, "08:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        8,
        0,
        tzinfo=NAIROBI,
    )

    requested_start = datetime(
        2026,
        7,
        28,
        9,
        0,
        tzinfo=NAIROBI,
    )

    with pytest.raises(AppointmentValidationError) as error:
        validate_appointment_start(
            requested_start,
            periods,
            now=current_time,
        )

    assert error.value.code == "DOCTOR_NOT_WORKING"


def test_time_during_break_is_rejected() -> None:
    periods = [
        working_period(0, "08:00", "12:00"),
        working_period(0, "13:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        8,
        0,
        tzinfo=NAIROBI,
    )

    requested_start = datetime(
        2026,
        7,
        27,
        12,
        30,
        tzinfo=NAIROBI,
    )

    with pytest.raises(AppointmentValidationError) as error:
        validate_appointment_start(
            requested_start,
            periods,
            now=current_time,
        )

    assert error.value.code == "INVALID_APPOINTMENT_SLOT"


def test_misaligned_slot_is_rejected() -> None:
    periods = [
        working_period(0, "08:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        8,
        0,
        tzinfo=NAIROBI,
    )

    requested_start = datetime(
        2026,
        7,
        27,
        9,
        15,
        tzinfo=NAIROBI,
    )

    with pytest.raises(AppointmentValidationError) as error:
        validate_appointment_start(
            requested_start,
            periods,
            now=current_time,
        )

    assert error.value.code == "INVALID_APPOINTMENT_SLOT"


def test_utc_datetime_is_normalized_to_nairobi() -> None:
    periods = [
        working_period(0, "08:00", "17:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        5,
        0,
        tzinfo=timezone.utc,
    )

    requested_start = datetime(
        2026,
        7,
        27,
        6,
        0,
        tzinfo=timezone.utc,
    )

    normalized_start = validate_appointment_start(
        requested_start,
        periods,
        now=current_time,
    )

    assert normalized_start.hour == 9
    assert normalized_start.utcoffset() is not None
    assert normalized_start.utcoffset().total_seconds() == 3 * 60 * 60


def test_availability_excludes_notice_window_and_booked_slots() -> None:
    periods = [
        working_period(0, "08:00", "11:00"),
    ]

    current_time = datetime(
        2026,
        7,
        27,
        7,
        15,
        tzinfo=NAIROBI,
    )

    booked_starts = [
        datetime(
            2026,
            7,
            27,
            9,
            0,
            tzinfo=NAIROBI,
        ),
    ]

    available_slots = get_available_slot_starts(
        MONDAY,
        periods,
        booked_starts,
        now=current_time,
    )

    assert [slot.time() for slot in available_slots] == [
        time(8, 30),
        time(9, 30),
        time(10, 0),
        time(10, 30),
    ]