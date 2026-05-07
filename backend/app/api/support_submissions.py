from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import SupportSubmissionCreate, SupportSubmissionResponse
from app.services.diagnostics import run_ticket_diagnostics
from app.services.lifecycle import add_history, apply_initial_sla

router = APIRouter(prefix="/support-submissions", tags=["support submissions"])


@router.post("", response_model=SupportSubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_support_submission(payload: SupportSubmissionCreate, db: Session = Depends(get_db)) -> SupportSubmissionResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        user = User(
            email=payload.email,
            full_name=payload.email.split("@")[0],
            role=UserRole.customer,
            password_hash="",
            is_active=True,
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            user = db.scalar(select(User).where(User.email == payload.email))
            if not user:
                raise

    ticket = Ticket(
        subject=payload.subject,
        description=payload.description,
        status=TicketStatus.open,
        priority=TicketPriority.normal,
        customer_id=user.id,
        requester_email=payload.email,
        company=payload.company,
        store=payload.store,
    )
    apply_initial_sla(ticket)
    db.add(ticket)
    db.flush()
    db.add(add_history(ticket, None, "created", None, "support submission", "created", {"source": "support_form"}))
    for diagnostic in run_ticket_diagnostics(ticket):
        db.add(diagnostic)
    db.add(add_history(ticket, None, "diagnostics", None, "run", "diagnostics_run", {"trigger": "support_submission"}))
    db.commit()
    return SupportSubmissionResponse(ticket_id=ticket.id, status=ticket.status, message="Support request submitted")
