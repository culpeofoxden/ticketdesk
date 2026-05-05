from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.models.ticket import Ticket, TicketComment, TicketHistory
from app.models.user import User
from app.schemas.ticket import CommentCreate, CommentRead, HistoryRead, TicketCreate, TicketDetail, TicketRead, TicketUpdate

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


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Ticket:
    ticket = Ticket(
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        customer_id=current_user.id,
    )
    db.add(ticket)
    db.flush()
    db.add(TicketHistory(ticket_id=ticket.id, actor_id=current_user.id, field="created", old_value=None, new_value="ticket"))
    db.commit()
    return load_ticket_or_404(ticket.id, db)


@router.get("", response_model=list[TicketRead])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    assignee_id: int | None = None,
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

    if current_user.role == UserRole.customer and (payload.status or "assignee_id" in changes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customers cannot assign or change status")

    if "assignee_id" in changes and payload.assignee_id is not None:
        assignee = db.get(User, payload.assignee_id)
        if not assignee or assignee.role not in {UserRole.admin, UserRole.agent}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be an agent or admin")

    for field, new_value in changes.items():
        old_value = getattr(ticket, field)
        if old_value == new_value:
            continue
        setattr(ticket, field, new_value)
        db.add(
            TicketHistory(
                ticket_id=ticket.id,
                actor_id=current_user.id,
                field=field,
                old_value=stringify(old_value),
                new_value=stringify(new_value),
            )
        )

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
    db.add(TicketHistory(ticket_id=ticket.id, actor_id=current_user.id, field="comment", old_value=None, new_value="added"))
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{ticket_id}/history", response_model=list[HistoryRead])
def get_history(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TicketHistory]:
    ticket = load_ticket_or_404(ticket_id, db)
    ensure_ticket_access(ticket, current_user)
    return sorted(ticket.history, key=lambda item: item.created_at, reverse=True)
