from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.clock import get_current_time
from app.main import app
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorWorkingHours,
    Patient,
)


NAIROBI = ZoneInfo("Africa/Nairobi")

FIXED_NOW = datetime(
    2026,
    7,
    27,
    8,
    0,
    tzinfo=NAIROBI,
)


def override_current_time(value: datetime = FIXED_NOW) -> None:
    """Set a deterministic application time for an API test."""

    app.dependency_overrides[get_current_time] = lambda: value


def create_doctor(
    database_session: Session,
    *,
    is_active: bool = True,
    weekday: int = 0,
    start_value: str = "08:00",
    end_value: str = "11:00",
) -> Doctor:
    doctor = Doctor(
        full_name="Dr. Availability Test",
        specialty="General Practice",
        is_active=is_active,
    )

    database_session.add(doctor)
    database_session.flush()

    database_session.add(
        DoctorWorkingHours(
            doctor_id=doctor.id,
            weekday=weekday,
            start_time=time.fromisoformat(start_value),
            end_time=time.fromisoformat(end_value),
        )
    )

    database_session.flush()

    return doctor


def create_patient(
    database_session: Session,
    *,
    email: str = "availability.patient@example.com",
) -> Patient:
    patient = Patient(
        full_name="Availability Test Patient",
        email=email,
        phone_number="+254700222222",
    )

    database_session.add(patient)
    database_session.flush()

    return patient


def test_returns_available_slots_for_doctor(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    response = client.get(
        f"/doctors/{doctor.id}/availability",
        params={"date": "2026-07-27"},
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["doctor_id"] == doctor.id
    assert response_body["doctor_name"] == doctor.full_name
    assert response_body["date"] == "2026-07-27"
    assert response_body["timezone"] == "Africa/Nairobi"
    assert response_body["slot_duration_minutes"] == 30

    assert response_body["available_slots"] == [
        {
            "start_at": "2026-07-27T09:00:00+03:00",
            "end_at": "2026-07-27T09:30:00+03:00",
        },
        {
            "start_at": "2026-07-27T09:30:00+03:00",
            "end_at": "2026-07-27T10:00:00+03:00",
        },
        {
            "start_at": "2026-07-27T10:00:00+03:00",
            "end_at": "2026-07-27T10:30:00+03:00",
        },
        {
            "start_at": "2026-07-27T10:30:00+03:00",
            "end_at": "2026-07-27T11:00:00+03:00",
        },
    ]


def test_scheduled_appointment_is_removed_from_availability(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    database_session.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            start_at=datetime(
                2026,
                7,
                27,
                9,
                30,
                tzinfo=NAIROBI,
            ),
            status=AppointmentStatus.SCHEDULED.value,
        )
    )

    database_session.flush()

    response = client.get(
        f"/doctors/{doctor.id}/availability",
        params={"date": "2026-07-27"},
    )

    assert response.status_code == 200

    returned_starts = [
        slot["start_at"]
        for slot in response.json()["available_slots"]
    ]

    assert "2026-07-27T09:30:00+03:00" not in returned_starts
    assert "2026-07-27T09:00:00+03:00" in returned_starts


def test_cancelled_appointment_does_not_block_availability(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    database_session.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            start_at=datetime(
                2026,
                7,
                27,
                9,
                30,
                tzinfo=NAIROBI,
            ),
            status=AppointmentStatus.CANCELLED.value,
            cancellation_reason="Patient cancelled.",
            cancelled_at=FIXED_NOW,
        )
    )

    database_session.flush()

    response = client.get(
        f"/doctors/{doctor.id}/availability",
        params={"date": "2026-07-27"},
    )

    assert response.status_code == 200

    returned_starts = [
        slot["start_at"]
        for slot in response.json()["available_slots"]
    ]

    assert "2026-07-27T09:30:00+03:00" in returned_starts


def test_non_working_day_returns_empty_list(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(
        database_session,
        weekday=1,
    )

    response = client.get(
        f"/doctors/{doctor.id}/availability",
        params={"date": "2026-07-27"},
    )

    assert response.status_code == 200
    assert response.json()["available_slots"] == []


def test_missing_doctor_returns_404(
    client: TestClient,
) -> None:
    override_current_time()

    response = client.get(
        "/doctors/999/availability",
        params={"date": "2026-07-27"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


def test_inactive_doctor_returns_409(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(
        database_session,
        is_active=False,
    )

    response = client.get(
        f"/doctors/{doctor.id}/availability",
        params={"date": "2026-07-27"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DOCTOR_INACTIVE"


def test_past_availability_date_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    response = client.get(
        f"/doctors/{doctor.id}/availability",
        params={"date": "2026-07-26"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "AVAILABILITY_DATE_IN_PAST"
    )


def test_missing_date_query_parameter_returns_422(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    response = client.get(
        f"/doctors/{doctor.id}/availability"
    )

    assert response.status_code == 422