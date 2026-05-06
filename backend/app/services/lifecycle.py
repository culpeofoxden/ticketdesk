from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.models.ticket import Ticket, TicketHistory
from app.models.user import User

SLA_POLICY: dict[TicketPriority, tuple[timedelta, timedelta]] = {
    TicketPriority.urgent: (timedelta(hours=1), timedelta(hours=8)),
    TicketPriority.high: (timedelta(hours=4), timedelta(hours=24)),
    TicketPriority.normal: (timedelta(hours=8), timedelta(hours=72)),
    TicketPriority.low: (timedelta(hours=24), timedelta(days=7)),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def apply_initial_sla(ticket: Ticket, now: datetime | None = None) -> None:
    now = now or utc_now()
    first_response_delta, resolution_delta = SLA_POLICY[ticket.priority]
    ticket.first_response_due_at = now + first_response_delta
    ticket.resolution_due_at = now + resolution_delta


def recalculate_sla_on_priority_change(ticket: Ticket, now: datetime | None = None) -> None:
    now = now or utc_now()
    first_response_delta, resolution_delta = SLA_POLICY[ticket.priority]
    if ticket.first_response_at is None:
        ticket.first_response_due_at = now + first_response_delta
    if ticket.status not in {TicketStatus.solved, TicketStatus.closed}:
        ticket.resolution_due_at = now + resolution_delta


def add_history(
    ticket: Ticket,
    actor: User | None,
    field: str,
    old_value: str | None,
    new_value: str | None,
    event_type: str,
    metadata: dict[str, Any] | None = None,
) -> TicketHistory:
    return TicketHistory(
        ticket_id=ticket.id,
        actor_id=actor.id if actor else None,
        field=field,
        old_value=old_value,
        new_value=new_value,
        event_type=event_type,
        event_metadata=metadata or {},
    )


def validate_status_transition(ticket: Ticket, actor: User, new_status: TicketStatus) -> None:
    if ticket.status == new_status:
        return

    if ticket.status == TicketStatus.closed and actor.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can reopen closed tickets")

    if actor.role == UserRole.customer:
        if ticket.customer_id != actor.id or new_status != TicketStatus.closed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customers can only close their own tickets")
        return

    if actor.role == UserRole.agent and new_status == TicketStatus.closed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agents cannot close tickets")


def apply_status_side_effects(ticket: Ticket, old_status: TicketStatus, new_status: TicketStatus) -> None:
    if old_status == new_status:
        return
    if new_status == TicketStatus.solved and ticket.solved_at is None:
        ticket.solved_at = utc_now()


def mark_first_response_if_needed(ticket: Ticket, actor: User) -> bool:
    if actor.role not in {UserRole.agent, UserRole.admin} or ticket.first_response_at is not None:
        return False
    ticket.first_response_at = utc_now()
    if ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.pending
    return True


def is_overdue(ticket: Ticket, now: datetime | None = None) -> bool:
    now = now or utc_now()
    first_response_overdue = ticket.first_response_at is None and ticket.first_response_due_at is not None and now > ticket.first_response_due_at
    resolution_overdue = ticket.status not in {TicketStatus.solved, TicketStatus.closed} and ticket.resolution_due_at is not None and now > ticket.resolution_due_at
    return first_response_overdue or resolution_overdue
