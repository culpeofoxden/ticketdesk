from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    created_at: datetime
    actor: UserRead | None

    model_config = ConfigDict(from_attributes=True)


class TicketRead(BaseModel):
    id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    customer: UserRead
    assignee: UserRead | None

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketRead):
    comments: list[CommentRead] = []
    history: list[HistoryRead] = []

