from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.clock import get_current_time
from app.main import app
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
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
    name: str,
    specialty: str,
) -> Doctor:
    doctor = Doctor(
        full_name=name,
        specialty=specialty,
        is_active=True,
    )

    database_session.add(doctor)
    database_session.flush()

    return doctor


def create_patient(
    database_session: Session,
    *,
    email: str,
) -> Patient:
    patient = Patient(
        full_name="Patient Appointments Test",
        email=email,
        phone_number="+254700555555",
    )

    database_session.add(patient)
    database_session.flush()

    return patient


def create_appointment(
    database_session: Session,
    *,
    doctor_id: int,
    patient_id: int,
    start_at: datetime,
    status: str = AppointmentStatus.SCHEDULED.value,
) -> Appointment:
    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        start_at=start_at,
        status=status,
        cancellation_reason=(
            "Patient cancelled."
            if status == AppointmentStatus.CANCELLED.value
            else None
        ),
        cancelled_at=(
            FIXED_NOW
            if status == AppointmentStatus.CANCELLED.value
            else None
        ),
    )

    database_session.add(appointment)
    database_session.flush()

    return appointment


def test_returns_upcoming_appointments_in_chronological_order(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    patient = create_patient(
        database_session,
        email="ordered.appointments@example.com",
    )

    first_doctor = create_doctor(
        database_session,
        name="Dr. First Appointment",
        specialty="General Practice",
    )

    second_doctor = create_doctor(
        database_session,
        name="Dr. Second Appointment",
        specialty="Paediatrics",
    )

    later_appointment = create_appointment(
        database_session,
        doctor_id=second_doctor.id,
        patient_id=patient.id,
        start_at=datetime(
            2026,
            7,
            27,
            11,
            0,
            tzinfo=NAIROBI,
        ),
    )

    earlier_appointment = create_appointment(
        database_session,
        doctor_id=first_doctor.id,
        patient_id=patient.id,
        start_at=datetime(
            2026,
            7,
            27,
            9,
            0,
            tzinfo=NAIROBI,
        ),
    )

    response = client.get(
        f"/patients/{patient.id}/appointments"
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["patient_id"] == patient.id
    assert response_body["patient_name"] == patient.full_name
    assert response_body["timezone"] == "Africa/Nairobi"

    returned_appointments = response_body["appointments"]

    assert [
        appointment["id"]
        for appointment in returned_appointments
    ] == [
        earlier_appointment.id,
        later_appointment.id,
    ]

    assert returned_appointments[0]["doctor_name"] == (
        "Dr. First Appointment"
    )

    assert returned_appointments[0]["doctor_specialty"] == (
        "General Practice"
    )

    assert returned_appointments[0]["start_at"] == (
        "2026-07-27T09:00:00+03:00"
    )

    assert returned_appointments[0]["end_at"] == (
        "2026-07-27T09:30:00+03:00"
    )


def test_past_appointments_are_excluded(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    patient = create_patient(
        database_session,
        email="past.appointments@example.com",
    )

    doctor = create_doctor(
        database_session,
        name="Dr. Past Appointment",
        specialty="General Practice",
    )

    create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_at=datetime(
            2026,
            7,
            27,
            7,
            30,
            tzinfo=NAIROBI,
        ),
    )

    future_appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_at=datetime(
            2026,
            7,
            27,
            9,
            0,
            tzinfo=NAIROBI,
        ),
    )

    response = client.get(
        f"/patients/{patient.id}/appointments"
    )

    assert response.status_code == 200

    returned_ids = [
        appointment["id"]
        for appointment in response.json()["appointments"]
    ]

    assert returned_ids == [future_appointment.id]


def test_cancelled_future_appointments_are_excluded(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    patient = create_patient(
        database_session,
        email="cancelled.future@example.com",
    )

    doctor = create_doctor(
        database_session,
        name="Dr. Cancelled Appointment",
        specialty="Dermatology",
    )

    create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_at=datetime(
            2026,
            7,
            27,
            9,
            0,
            tzinfo=NAIROBI,
        ),
        status=AppointmentStatus.CANCELLED.value,
    )

    scheduled_appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_at=datetime(
            2026,
            7,
            27,
            10,
            0,
            tzinfo=NAIROBI,
        ),
    )

    response = client.get(
        f"/patients/{patient.id}/appointments"
    )

    assert response.status_code == 200

    returned_ids = [
        appointment["id"]
        for appointment in response.json()["appointments"]
    ]

    assert returned_ids == [scheduled_appointment.id]


def test_patient_with_no_upcoming_appointments_returns_empty_list(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    patient = create_patient(
        database_session,
        email="empty.appointments@example.com",
    )

    response = client.get(
        f"/patients/{patient.id}/appointments"
    )

    assert response.status_code == 200
    assert response.json()["appointments"] == []


def test_missing_patient_returns_404(
    client: TestClient,
) -> None:
    override_current_time()

    response = client.get(
        "/patients/999/appointments"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_invalid_patient_id_returns_422(
    client: TestClient,
) -> None:
    override_current_time()

    response = client.get(
        "/patients/0/appointments"
    )

    assert response.status_code == 422