from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import func, select
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


def create_doctor(database_session: Session) -> Doctor:
    doctor = Doctor(
        full_name="Dr. Cancellation API Test",
        specialty="General Practice",
        is_active=True,
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
    email: str,
) -> Patient:
    patient = Patient(
        full_name="Cancellation Test Patient",
        email=email,
        phone_number="+254700333333",
    )

    database_session.add(patient)
    database_session.flush()

    return patient


def create_scheduled_appointment(
    database_session: Session,
    *,
    doctor_id: int,
    patient_id: int,
) -> Appointment:
    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        start_at=datetime(
            2026,
            7,
            27,
            9,
            0,
            tzinfo=NAIROBI,
        ),
        status=AppointmentStatus.SCHEDULED.value,
    )

    database_session.add(appointment)
    database_session.flush()

    return appointment


def test_cancel_appointment_successfully(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="successful.cancel@example.com",
    )

    appointment = create_scheduled_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={
            "reason": "Patient is no longer available.",
        },
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["id"] == appointment.id
    assert response_body["status"] == "cancelled"
    assert response_body["cancellation_reason"] == (
        "Patient is no longer available."
    )
    assert response_body["cancelled_at"] == (
        "2026-07-27T08:00:00+03:00"
    )

    database_session.refresh(appointment)

    assert appointment.status == AppointmentStatus.CANCELLED.value
    assert appointment.cancellation_reason == (
        "Patient is no longer available."
    )
    assert appointment.cancelled_at is not None


def test_repeated_cancellation_returns_409(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="repeat.cancel@example.com",
    )

    appointment = create_scheduled_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
    )

    first_response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": "First cancellation request."},
    )

    second_response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": "Second cancellation request."},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == (
        "APPOINTMENT_ALREADY_CANCELLED"
    )


def test_missing_appointment_returns_404(
    client: TestClient,
) -> None:
    override_current_time()

    response = client.patch(
        "/appointments/999/cancel",
        json={"reason": "Unable to attend."},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == (
        "APPOINTMENT_NOT_FOUND"
    )


def test_blank_cancellation_reason_returns_422(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="blank.reason@example.com",
    )

    appointment = create_scheduled_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": "   "},
    )

    assert response.status_code == 422


def test_unexpected_cancellation_property_returns_422(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="extra.property@example.com",
    )

    appointment = create_scheduled_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={
            "reason": "Patient is unable to attend.",
            "delete_permanently": True,
        },
    )

    assert response.status_code == 422


def test_cancellation_releases_slot_for_another_patient(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    original_patient = create_patient(
        database_session,
        email="original.patient@example.com",
    )

    replacement_patient = create_patient(
        database_session,
        email="replacement.patient@example.com",
    )

    original_appointment = create_scheduled_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=original_patient.id,
    )

    cancellation_response = client.patch(
        f"/appointments/{original_appointment.id}/cancel",
        json={"reason": "Original patient cannot attend."},
    )

    replacement_response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": replacement_patient.id,
            "start_at": "2026-07-27T09:00:00+03:00",
        },
    )

    assert cancellation_response.status_code == 200
    assert replacement_response.status_code == 201

    scheduled_count = database_session.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.doctor_id == doctor.id,
            Appointment.start_at
            == datetime(
                2026,
                7,
                27,
                9,
                0,
                tzinfo=NAIROBI,
            ),
            Appointment.status
            == AppointmentStatus.SCHEDULED.value,
        )
    )

    cancelled_count = database_session.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.doctor_id == doctor.id,
            Appointment.start_at
            == datetime(
                2026,
                7,
                27,
                9,
                0,
                tzinfo=NAIROBI,
            ),
            Appointment.status
            == AppointmentStatus.CANCELLED.value,
        )
    )

    assert scheduled_count == 1
    assert cancelled_count == 1