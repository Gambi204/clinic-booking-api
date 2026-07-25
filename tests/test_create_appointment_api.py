from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import get_current_time
from app.main import app
from app.models import (
    Appointment,
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
    """Override the API clock with a deterministic test value."""

    app.dependency_overrides[get_current_time] = lambda: value


def create_doctor(
    database_session: Session,
    *,
    is_active: bool = True,
) -> Doctor:
    doctor = Doctor(
        full_name="Dr. API Test",
        specialty="General Practice",
        is_active=is_active,
    )

    database_session.add(doctor)
    database_session.flush()

    database_session.add(
        DoctorWorkingHours(
            doctor_id=doctor.id,
            weekday=0,
            start_time=time(8, 0),
            end_time=time(17, 0),
        )
    )

    database_session.flush()

    return doctor


def create_patient(
    database_session: Session,
    *,
    email: str = "api.patient@example.com",
) -> Patient:
    patient = Patient(
        full_name="API Test Patient",
        email=email,
        phone_number="+254700111111",
    )

    database_session.add(patient)
    database_session.flush()

    return patient


def valid_payload(
    doctor_id: int,
    patient_id: int,
) -> dict[str, int | str]:
    return {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "start_at": "2026-07-27T09:00:00+03:00",
    }


def test_create_appointment_successfully(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json=valid_payload(doctor.id, patient.id),
    )

    assert response.status_code == 201

    response_body = response.json()

    assert response_body["doctor_id"] == doctor.id
    assert response_body["patient_id"] == patient.id
    assert response_body["status"] == "scheduled"
    assert response_body["start_at"] == (
        "2026-07-27T09:00:00+03:00"
    )
    assert response_body["end_at"] == (
        "2026-07-27T09:30:00+03:00"
    )

    appointment_count = database_session.scalar(
        select(func.count()).select_from(Appointment)
    )

    assert appointment_count == 1


def test_missing_doctor_returns_404(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json=valid_payload(999, patient.id),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


def test_missing_patient_returns_404(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    response = client.post(
        "/appointments",
        json=valid_payload(doctor.id, 999),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_inactive_doctor_returns_409(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(
        database_session,
        is_active=False,
    )
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json=valid_payload(doctor.id, patient.id),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DOCTOR_INACTIVE"


def test_naive_appointment_timestamp_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "start_at": "2026-07-27T09:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TIMEZONE_REQUIRED"


def test_past_appointment_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "start_at": "2026-07-27T07:30:00+03:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "APPOINTMENT_NOT_IN_FUTURE"
    )


def test_minimum_notice_violation_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "start_at": "2026-07-27T08:30:00+03:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "MINIMUM_NOTICE_NOT_MET"
    )


def test_outside_working_hours_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "start_at": "2026-07-27T17:00:00+03:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "INVALID_APPOINTMENT_SLOT"
    )


def test_misaligned_appointment_slot_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "start_at": "2026-07-27T09:15:00+03:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "INVALID_APPOINTMENT_SLOT"
    )


def test_duplicate_booking_returns_409(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    first_patient = create_patient(
        database_session,
        email="first.api.patient@example.com",
    )

    second_patient = create_patient(
        database_session,
        email="second.api.patient@example.com",
    )

    first_response = client.post(
        "/appointments",
        json=valid_payload(doctor.id, first_patient.id),
    )

    second_response = client.post(
        "/appointments",
        json=valid_payload(doctor.id, second_patient.id),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == (
        "SLOT_UNAVAILABLE"
    )

    appointment_count = database_session.scalar(
        select(func.count()).select_from(Appointment)
    )

    assert appointment_count == 1


def test_unexpected_request_property_returns_422(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)
    patient = create_patient(database_session)

    payload = valid_payload(doctor.id, patient.id)
    payload["unexpected_property"] = "not allowed"

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 422