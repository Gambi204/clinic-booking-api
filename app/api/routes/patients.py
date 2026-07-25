from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.core.clock import get_current_time
from app.core.config import settings
from app.db.dependencies import get_db
from app.schemas import (
    ErrorResponse,
    PatientAppointmentItem,
    PatientAppointmentsResponse,
)
from app.services import (
    ResourceNotFoundError,
    get_upcoming_patient_appointments,
    normalize_to_clinic_timezone,
)


router = APIRouter(tags=["Patients"])


@router.get(
    "/patients/{patient_id}/appointments",
    response_model=PatientAppointmentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get upcoming patient appointments",
    description=(
        "Return the patient's upcoming scheduled appointments "
        "ordered from earliest to latest."
    ),
    responses={
        404: {
            "model": ErrorResponse,
            "description": "The patient does not exist.",
        },
    },
)
def get_patient_appointments(
    patient_id: Annotated[
        int,
        Path(
            gt=0,
            description="Identifier of the patient.",
        ),
    ],
    database_session: Annotated[Session, Depends(get_db)],
    current_time: Annotated[datetime, Depends(get_current_time)],
) -> PatientAppointmentsResponse:
    """Return upcoming scheduled appointments for a patient."""

    try:
        patient, appointments = get_upcoming_patient_appointments(
            database_session,
            patient_id=patient_id,
            now=current_time,
        )
    except ResourceNotFoundError as error:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=error.code,
            message=error.message,
        ) from error

    slot_duration = timedelta(
        minutes=settings.slot_duration_minutes,
    )

    appointment_items: list[PatientAppointmentItem] = []

    for appointment in appointments:
        normalized_start = normalize_to_clinic_timezone(
            appointment.start_at,
        )

        appointment_items.append(
            PatientAppointmentItem(
                id=appointment.id,
                doctor_id=appointment.doctor_id,
                doctor_name=appointment.doctor.full_name,
                doctor_specialty=appointment.doctor.specialty,
                start_at=normalized_start,
                end_at=normalized_start + slot_duration,
                status=appointment.status,
            )
        )

    return PatientAppointmentsResponse(
        patient_id=patient.id,
        patient_name=patient.full_name,
        timezone=settings.clinic_timezone,
        appointments=appointment_items,
    )