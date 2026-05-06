from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.models.ticket import Ticket, TicketComment, TicketHistory
from app.models.user import User
from app.schemas.ticket import CommentCreate, CommentRead, HistoryRead, TicketCreate, TicketDetail, TicketRead, TicketUpdate
from app.services.lifecycle import (
    add_history,
    apply_initial_sla,
    apply_status_side_effects,
    mark_first_response_if_needed,
    recalculate_sla_on_priority_change,
    utc_now,
    validate_status_transition,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


def ensure_ticket_access(ticket: Ticket, user: User) -> None:
    if user.role in {UserRole.admin, UserRole.agent}:
        return
    if ticket.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket is not available")


def load_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(
            joinedload(Ticket.customer),
            joinedload(Ticket.assignee),
            selectinload(Ticket.comments).joinedload(TicketComment.author),
            selectinload(Ticket.history).joinedload(TicketHistory.actor),
        )
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def stringify(value: object) -> str | None:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def history_event_type(field: str) -> str:
    return {
        "status": "status_changed",
        "priority": "priority_changed",
        "assignee_id": "assigned",
        "created": "created",
        "comment": "comment_added",
    }.get(field, "ticket_updated")


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Ticket:
    ticket = Ticket(
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        customer_id=current_user.id,
    )
    apply_initial_sla(ticket)
    db.add(ticket)
    db.flush()
    db.add(add_history(ticket, current_user, "created", None, "ticket", "created", {"source": "app"}))
    db.commit()
    return load_ticket_or_404(ticket.id, db)


@router.get("", response_model=list[TicketRead])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    assignee_id: int | None = None,
    queue: str | None = Query(default=None, pattern="^(unassigned|my|urgent|overdue|pending)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Ticket]:
    query = select(Ticket).options(joinedload(Ticket.customer), joinedload(Ticket.assignee)).order_by(Ticket.updated_at.desc())
    if current_user.role == UserRole.customer:
        query = query.where(Ticket.customer_id == current_user.id)
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if priority:
        query = query.where(Ticket.priority == priority)
    if assignee_id:
        query = query.where(Ticket.assignee_id == assignee_id)
    if queue == "unassigned":
        query = query.where(Ticket.assignee_id.is_(None), Ticket.status != TicketStatus.closed)
    elif queue == "my":
        query = query.where(Ticket.assignee_id == current_user.id)
    elif queue == "urgent":
        query = query.where(Ticket.priority == TicketPriority.urgent, Ticket.status.not_in([TicketStatus.solved, TicketStatus.closed]))
    elif queue == "pending":
        query = query.where(Ticket.status == TicketStatus.pending)
    elif queue == "overdue":
        now = utc_now()
        query = query.where(
            or_(
                (Ticket.first_response_at.is_(None) & Ticket.first_response_due_at.is_not(None) & (Ticket.first_response_due_at < now)),
                (Ticket.status.not_in([TicketStatus.solved, TicketStatus.closed]) & Ticket.resolution_due_at.is_not(None) & (Ticket.resolution_due_at < now)),
            )
        )
    return list(db.scalars(query))


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Ticket:
    ticket = load_ticket_or_404(ticket_id, db)
    ensure_ticket_access(ticket, current_user)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Ticket:
    ticket = load_ticket_or_404(ticket_id, db)
    ensure_ticket_access(ticket, current_user)

    changes = payload.model_dump(exclude_unset=True)

    if current_user.role == UserRole.customer and "assignee_id" in changes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customers cannot assign tickets")

    if current_user.role == UserRole.customer and "priority" in changes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customers cannot change priority")

    if "status" in changes and payload.status is not None:
        validate_status_transition(ticket, current_user, payload.status)

    if "assignee_id" in changes and payload.assignee_id is not None:
        assignee = db.get(User, payload.assignee_id)
        if not assignee or assignee.role not in {UserRole.admin, UserRole.agent} or not assignee.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be an active agent or admin")

    for field, new_value in changes.items():
        old_value = getattr(ticket, field)
        if old_value == new_value:
            continue
        setattr(ticket, field, new_value)
        if field == "priority":
            recalculate_sla_on_priority_change(ticket)
        if field == "status":
            apply_status_side_effects(ticket, old_value, new_value)
        metadata = {"field": field}
        if field == "assignee_id":
            assignee = db.get(User, new_value) if new_value else None
            metadata["assignee_name"] = assignee.full_name if assignee else None
        db.add(add_history(ticket, current_user, field, stringify(old_value), stringify(new_value), history_event_type(field), metadata))

    db.commit()
    return load_ticket_or_404(ticket.id, db)


@router.post("/{ticket_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketComment:
    ticket = load_ticket_or_404(ticket_id, db)
    ensure_ticket_access(ticket, current_user)
    comment = TicketComment(ticket_id=ticket.id, author_id=current_user.id, body=payload.body)
    db.add(comment)
    first_response_marked = mark_first_response_if_needed(ticket, current_user)
    db.flush()
    db.add(
        add_history(
            ticket,
            current_user,
            "comment",
            None,
            "added",
            "comment_added",
            {"comment_id": comment.id, "first_response": first_response_marked},
        )
    )
    if first_response_marked:
        db.add(add_history(ticket, current_user, "first_response_at", None, stringify(ticket.first_response_at), "first_response_recorded"))
        if ticket.status == TicketStatus.pending:
            db.add(add_history(ticket, current_user, "status", "open", "pending", "status_changed", {"reason": "first_response"}))
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{ticket_id}/history", response_model=list[HistoryRead])
def get_history(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TicketHistory]:
    ticket = load_ticket_or_404(ticket_id, db)
    ensure_ticket_access(ticket, current_user)
    return sorted(ticket.history, key=lambda item: item.created_at, reverse=True)
