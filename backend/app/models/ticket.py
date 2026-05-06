from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import TicketPriority, TicketStatus


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subject: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.open, index=True)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority), default=TicketPriority.normal, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    requester_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    store: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("User", back_populates="created_tickets", foreign_keys=[customer_id])
    assignee = relationship("User", back_populates="assigned_tickets", foreign_keys=[assignee_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.created_at.desc()")


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="comments")


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    field: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="history")
    actor = relationship("User")
