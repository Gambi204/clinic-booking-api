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
) -> Doctor:
    doctor = Doctor(
        full_name="Dr. Rescheduling API Test",
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
    email: str,
) -> Patient:
    patient = Patient(
        full_name="Rescheduling Test Patient",
        email=email,
        phone_number="+254700444444",
    )

    database_session.add(patient)
    database_session.flush()

    return patient


def create_appointment(
    database_session: Session,
    *,
    doctor_id: int,
    patient_id: int,
    hour: int,
    status: str = AppointmentStatus.SCHEDULED.value,
) -> Appointment:
    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        start_at=datetime(
            2026,
            7,
            27,
            hour,
            0,
            tzinfo=NAIROBI,
        ),
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


def test_reschedule_appointment_successfully(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="successful.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        hour=9,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["id"] == appointment.id
    assert response_body["status"] == "scheduled"
    assert response_body["previous_start_at"] == (
        "2026-07-27T09:00:00+03:00"
    )
    assert response_body["start_at"] == (
        "2026-07-27T10:00:00+03:00"
    )
    assert response_body["end_at"] == (
        "2026-07-27T10:30:00+03:00"
    )

    database_session.refresh(appointment)

    assert appointment.start_at.astimezone(NAIROBI) == datetime(
        2026,
        7,
        27,
        10,
        0,
        tzinfo=NAIROBI,
    )


def test_rescheduling_releases_original_slot(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    original_patient = create_patient(
        database_session,
        email="original.reschedule@example.com",
    )

    replacement_patient = create_patient(
        database_session,
        email="replacement.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=original_patient.id,
        hour=9,
    )

    reschedule_response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    replacement_response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": replacement_patient.id,
            "start_at": "2026-07-27T09:00:00+03:00",
        },
    )

    assert reschedule_response.status_code == 200
    assert replacement_response.status_code == 201


def test_rescheduled_destination_slot_becomes_unavailable(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    original_patient = create_patient(
        database_session,
        email="destination.original@example.com",
    )

    second_patient = create_patient(
        database_session,
        email="destination.second@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=original_patient.id,
        hour=9,
    )

    reschedule_response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    conflicting_response = client.post(
        "/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_id": second_patient.id,
            "start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    assert reschedule_response.status_code == 200
    assert conflicting_response.status_code == 409
    assert conflicting_response.json()["error"]["code"] == (
        "SLOT_UNAVAILABLE"
    )


def test_occupied_destination_returns_409_and_keeps_original_slot(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    first_patient = create_patient(
        database_session,
        email="occupied.first@example.com",
    )

    second_patient = create_patient(
        database_session,
        email="occupied.second@example.com",
    )

    appointment_to_move = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=first_patient.id,
        hour=9,
    )

    create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=second_patient.id,
        hour=10,
    )

    response = client.patch(
        f"/appointments/{appointment_to_move.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_UNAVAILABLE"

    database_session.refresh(appointment_to_move)

    assert appointment_to_move.start_at.astimezone(NAIROBI) == datetime(
        2026,
        7,
        27,
        9,
        0,
        tzinfo=NAIROBI,
    )


def test_cancelled_appointment_cannot_be_rescheduled(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="cancelled.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        hour=9,
        status=AppointmentStatus.CANCELLED.value,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "CANCELLED_APPOINTMENT_CANNOT_BE_RESCHEDULED"
    )


def test_missing_appointment_returns_404(
    client: TestClient,
) -> None:
    override_current_time()

    response = client.patch(
        "/appointments/999/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == (
        "APPOINTMENT_NOT_FOUND"
    )


def test_same_time_returns_409(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="unchanged.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        hour=9,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T09:00:00+03:00",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "APPOINTMENT_TIME_UNCHANGED"
    )


def test_invalid_new_time_preserves_original_appointment(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="invalid.time.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        hour=9,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T08:30:00+03:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "MINIMUM_NOTICE_NOT_MET"
    )

    database_session.refresh(appointment)

    assert appointment.start_at.astimezone(NAIROBI) == datetime(
        2026,
        7,
        27,
        9,
        0,
        tzinfo=NAIROBI,
    )


def test_naive_new_timestamp_returns_400(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="naive.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        hour=9,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TIMEZONE_REQUIRED"


def test_unexpected_reschedule_property_returns_422(
    client: TestClient,
    database_session: Session,
) -> None:
    override_current_time()

    doctor = create_doctor(database_session)

    patient = create_patient(
        database_session,
        email="extra.reschedule@example.com",
    )

    appointment = create_appointment(
        database_session,
        doctor_id=doctor.id,
        patient_id=patient.id,
        hour=9,
    )

    response = client.patch(
        f"/appointments/{appointment.id}/reschedule",
        json={
            "new_start_at": "2026-07-27T10:00:00+03:00",
            "force": True,
        },
    )

    assert response.status_code == 422