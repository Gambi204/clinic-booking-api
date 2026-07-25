from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.core.clock import get_current_time
from app.core.config import settings
from app.db.dependencies import get_db
from app.schemas import (
    AppointmentCancellationResponse,
    AppointmentCancelRequest,
    AppointmentCreate,
    AppointmentRescheduleRequest,
    AppointmentRescheduleResponse,
    AppointmentResponse,
    ErrorResponse,
)
from app.services import (
    AppointmentConflictError,
    AppointmentValidationError,
    ResourceNotFoundError,
    cancel_appointment,
    create_appointment,
    normalize_to_clinic_timezone,
    reschedule_appointment,
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


@router.patch(
    "/appointments/{appointment_id}/cancel",
    response_model=AppointmentCancellationResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an appointment",
    description=(
        "Cancel a scheduled appointment and release its booking slot."
    ),
    responses={
        404: {
            "model": ErrorResponse,
            "description": "The appointment does not exist.",
        },
        409: {
            "model": ErrorResponse,
            "description": "The appointment is already cancelled.",
        },
    },
)
def cancel_existing_appointment(
    appointment_id: Annotated[
        int,
        Path(
            gt=0,
            description="Identifier of the appointment to cancel.",
        ),
    ],
    payload: AppointmentCancelRequest,
    database_session: Annotated[Session, Depends(get_db)],
    current_time: Annotated[datetime, Depends(get_current_time)],
) -> AppointmentCancellationResponse:
    """Cancel a scheduled appointment without deleting its record."""

    try:
        appointment = cancel_appointment(
            database_session,
            appointment_id=appointment_id,
            reason=payload.reason,
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

    normalized_start = normalize_to_clinic_timezone(
        appointment.start_at,
    )

    normalized_cancelled_at = normalize_to_clinic_timezone(
        appointment.cancelled_at,
        field_name="cancelled_at",
    )

    normalized_updated_at = normalize_to_clinic_timezone(
        appointment.updated_at,
        field_name="updated_at",
    )

    return AppointmentCancellationResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        start_at=normalized_start,
        end_at=normalized_start
        + timedelta(minutes=settings.slot_duration_minutes),
        status=appointment.status,
        cancellation_reason=appointment.cancellation_reason,
        cancelled_at=normalized_cancelled_at,
        updated_at=normalized_updated_at,
    )

@router.patch(
    "/appointments/{appointment_id}/reschedule",
    response_model=AppointmentRescheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Reschedule an appointment",
    description=(
        "Move a scheduled appointment to another valid and "
        "available slot."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "The new time violates an appointment scheduling rule."
            ),
        },
        404: {
            "model": ErrorResponse,
            "description": "The appointment or doctor does not exist.",
        },
        409: {
            "model": ErrorResponse,
            "description": (
                "The appointment cannot be moved to the requested slot."
            ),
        },
    },
)
def reschedule_existing_appointment(
    appointment_id: Annotated[
        int,
        Path(
            gt=0,
            description="Identifier of the appointment to reschedule.",
        ),
    ],
    payload: AppointmentRescheduleRequest,
    database_session: Annotated[Session, Depends(get_db)],
    current_time: Annotated[datetime, Depends(get_current_time)],
) -> AppointmentRescheduleResponse:
    """Move an appointment atomically to another valid slot."""

    try:
        appointment, previous_start = reschedule_appointment(
            database_session,
            appointment_id=appointment_id,
            requested_start=payload.new_start_at,
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
        appointment.start_at,
    )

    normalized_updated_at = normalize_to_clinic_timezone(
        appointment.updated_at,
        field_name="updated_at",
    )

    return AppointmentRescheduleResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        previous_start_at=previous_start,
        start_at=normalized_start,
        end_at=normalized_start
        + timedelta(minutes=settings.slot_duration_minutes),
        status=appointment.status,
        updated_at=normalized_updated_at,
    )