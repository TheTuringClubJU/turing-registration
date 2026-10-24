"""
app/registrations/router.py

FastAPI router for event registrations:
POST /events/{slug}/register
Handles HTTP status codes:
- 201: Registration created successfully
- 404: Event slug not found
- 409: Closed event window, inactive event, or duplicate email submissions
- 422: Input validation failure with field-level errors
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.attendance import qr
from app.core.database import get_db
from app.email_templates import send
from app.registrations import crud
from app.registrations.schemas import RegistrationCreate, RegistrationOut
from app.registrations.validators import RegistrationValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["registrations"])


def _send_confirmation_background(
    to_email: str,
    event_dict: dict[str, Any],
    team_name: str | None,
    participants_dict: list[dict[str, Any]],
    registration_id_str: str,
    ticket_code: str | None = None,
) -> None:
    """
    Background worker: generates QR PNG and sends confirmation email.
    Any failure is caught and logged safely without logging participant PII or API keys.
    """
    try:
        # Providers belong to Sukrit (QR) and Darsh (email). Do not implement
        # attendance or silently claim delivery while their modules are pending.
        generate_image = getattr(qr, "generate_image", None)
        send_confirmation = getattr(send, "send_registration_confirmation", None)
        if generate_image is None or send_confirmation is None:
            logger.warning("Confirmation pending: QR/email provider has not been integrated.")
            return
        # Encode registration_id_str for backwards-compatible verification with attendance QR endpoint
        qr_bytes = generate_image(registration_id_str)
        send_confirmation(
            to=to_email,
            event=event_dict,
            team_name=team_name,
            participants=participants_dict,
            qr_bytes=qr_bytes,
            registration_id=registration_id_str,
        )
    except Exception as exc:
        logger.error(
            "Background confirmation task failed: %s",
            type(exc).__name__,
        )


@router.post(
    "/{slug}/register",
    response_model=RegistrationOut,
    status_code=status.HTTP_201_CREATED,
)
def register_for_event(
    slug: str,
    data: RegistrationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RegistrationOut:
    """
    Public registration endpoint:
    - Resolves event by slug under row-level lock.
    - Rechecks opening time window and active status.
    - Validates participant count, team rules, lead requirements, and email uniqueness.
    - Atomically writes Registration and Attendance records in a single transaction.
    - Enqueues non-blocking confirmation email with inline QR code in BackgroundTasks.
    """
    try:
        registration, event, normalized = crud.create_registration(db, slug, data)
    except crud.EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except crud.EventClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except crud.DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except RegistrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors,
        ) from None
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration conflict or constraint violation",
        ) from None

    # Select primary contact for confirmation email (lead or first participant)
    lead = next(
        (p for p in normalized.participants if p.is_team_lead),
        normalized.participants[0],
    )

    event_dict = {
        "name": event.name,
        "event_code": event.event_code,
        "slug": event.slug,
    }
    participants_dict = [p.model_dump() for p in normalized.participants]

    background_tasks.add_task(
        _send_confirmation_background,
        to_email=lead.email,
        event_dict=event_dict,
        team_name=registration.team_name,
        participants_dict=participants_dict,
        registration_id_str=str(registration.id),
        ticket_code=getattr(registration, "ticket_code", None),
    )

    return RegistrationOut.model_validate(registration)
