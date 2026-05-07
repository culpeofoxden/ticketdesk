from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.user import UserRead


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)
    priority: TicketPriority = TicketPriority.normal


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=3)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assignee_id: int | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)


class CommentRead(BaseModel):
    id: int
    body: str
    created_at: datetime
    author: UserRead

    model_config = ConfigDict(from_attributes=True)


class HistoryRead(BaseModel):
    id: int
    field: str
    old_value: str | None
    new_value: str | None
    event_type: str | None
    event_metadata: dict | None
    created_at: datetime
    actor: UserRead | None

    model_config = ConfigDict(from_attributes=True)


class DiagnosticRead(BaseModel):
    id: int
    intent: str
    playbook: str
    check_name: str
    service: str
    status: str
    severity: str
    summary: str
    details: dict | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketRead(BaseModel):
    id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    requester_email: EmailStr | None
    company: str | None
    store: str | None
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    first_response_at: datetime | None
    solved_at: datetime | None
    customer: UserRead
    assignee: UserRead | None

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketRead):
    comments: list[CommentRead] = []
    history: list[HistoryRead] = []


class SupportSubmissionCreate(BaseModel):
    email: EmailStr
    company: str = Field(min_length=1, max_length=255)
    store: str = Field(min_length=1, max_length=255)
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)


class SupportSubmissionResponse(BaseModel):
    ticket_id: int
    status: TicketStatus
    message: str
