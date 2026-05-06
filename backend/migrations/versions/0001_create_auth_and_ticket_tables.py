"""create auth and ticket tables

Revision ID: 0001_auth_ticket_tables
Revises:
Create Date: 2026-04-27 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0001_auth_ticket_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = sa.Enum("admin", "agent", "customer", name="userrole")
ticket_status = sa.Enum("open", "pending", "solved", "closed", name="ticketstatus")
ticket_priority = sa.Enum("low", "normal", "high", "urgent", name="ticketpriority")


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if "users" in inspector.get_table_names():
        return

    user_role.create(op.get_bind(), checkfirst=True)
    ticket_status.create(op.get_bind(), checkfirst=True)
    ticket_priority.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("priority", ticket_priority, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("requester_email", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("store", sa.String(length=255), nullable=True),
        sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_assignee_id"), "tickets", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_tickets_id"), "tickets", ["id"], unique=False)
    op.create_index(op.f("ix_tickets_priority"), "tickets", ["priority"], unique=False)
    op.create_index(op.f("ix_tickets_requester_email"), "tickets", ["requester_email"], unique=False)
    op.create_index(op.f("ix_tickets_status"), "tickets", ["status"], unique=False)
    op.create_index(op.f("ix_tickets_subject"), "tickets", ["subject"], unique=False)

    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticket_comments_id"), "ticket_comments", ["id"], unique=False)
    op.create_index(op.f("ix_ticket_comments_ticket_id"), "ticket_comments", ["ticket_id"], unique=False)

    op.create_table(
        "ticket_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("field", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticket_history_id"), "ticket_history", ["id"], unique=False)
    op.create_index(op.f("ix_ticket_history_event_type"), "ticket_history", ["event_type"], unique=False)
    op.create_index(op.f("ix_ticket_history_ticket_id"), "ticket_history", ["ticket_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ticket_history_ticket_id"), table_name="ticket_history")
    op.drop_index(op.f("ix_ticket_history_id"), table_name="ticket_history")
    op.drop_table("ticket_history")

    op.drop_index(op.f("ix_ticket_comments_ticket_id"), table_name="ticket_comments")
    op.drop_index(op.f("ix_ticket_comments_id"), table_name="ticket_comments")
    op.drop_table("ticket_comments")

    op.drop_index(op.f("ix_tickets_subject"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_status"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_priority"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_id"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_assignee_id"), table_name="tickets")
    op.drop_table("tickets")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    ticket_priority.drop(op.get_bind(), checkfirst=True)
    ticket_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
