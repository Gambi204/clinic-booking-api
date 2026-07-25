from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.core.clock import get_current_time
from app.core.config import settings
from app.db.dependencies import get_db
from app.schemas import (
    AppointmentCreate,
    AppointmentResponse,
    ErrorResponse,
)
from app.services import (
    AppointmentConflictError,
    AppointmentValidationError,
    ResourceNotFoundError,
    create_appointment,
    normalize_to_clinic_timezone,
)


router = APIRouter(tags=["Appointments"])


@router.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment",
    description=(
        "Create a scheduled 30-minute appointment with a doctor."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": "The requested time violates a booking rule.",
        },
        404: {
            "model": ErrorResponse,
            "description": "The doctor or patient does not exist.",
        },
        409: {
            "model": ErrorResponse,
            "description": (
                "The doctor is inactive or the slot is unavailable."
            ),
        },
    },
)
def book_appointment(
    payload: AppointmentCreate,
    database_session: Annotated[Session, Depends(get_db)],
    current_time: Annotated[datetime, Depends(get_current_time)],
) -> AppointmentResponse:
    """Book an appointment after validating all scheduling rules."""

    try:
        appointment = create_appointment(
            database_session,
            doctor_id=payload.doctor_id,
            patient_id=payload.patient_id,
            requested_start=payload.start_at,
            now=current_time,
        )
    except ResourceNotFoundError as error:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=error.code,
            message=error.message,
        ) from error
    except AppointmentConflictError as error:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code=error.code,
            message=error.message,
        ) from error
    except AppointmentValidationError as error:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=error.code,
            message=error.message,
        ) from error

    normalized_start = normalize_to_clinic_timezone(
        appointment.start_at
    )

    normalized_created_at = normalize_to_clinic_timezone(
        appointment.created_at,
        field_name="created_at",
    )

    return AppointmentResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        start_at=normalized_start,
        end_at=normalized_start
        + timedelta(minutes=settings.slot_duration_minutes),
        status=appointment.status,
        created_at=normalized_created_at,
    )