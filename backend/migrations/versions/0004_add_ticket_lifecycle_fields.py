"""add ticket lifecycle fields

Revision ID: 0004_ticket_lifecycle
Revises: 0003_support_fields
Create Date: 2026-05-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0004_ticket_lifecycle"
down_revision: Union[str, None] = "0003_support_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def add_column_if_missing(table: str, name: str, column: sa.Column) -> None:
    columns = {item["name"] for item in inspect(op.get_bind()).get_columns(table)}
    if name not in columns:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("tickets", "first_response_due_at", sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("tickets", "resolution_due_at", sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("tickets", "first_response_at", sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("tickets", "solved_at", sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("ticket_history", "event_type", sa.Column("event_type", sa.String(length=100), nullable=True))
    add_column_if_missing("ticket_history", "event_metadata", sa.Column("event_metadata", sa.JSON(), nullable=True))
    indexes = {item["name"] for item in inspect(op.get_bind()).get_indexes("ticket_history")}
    if op.f("ix_ticket_history_event_type") not in indexes:
        op.create_index(op.f("ix_ticket_history_event_type"), "ticket_history", ["event_type"], unique=False)
    op.execute(
        """
        UPDATE tickets
        SET
            first_response_due_at = COALESCE(
                first_response_due_at,
                created_at + CASE priority::text
                    WHEN 'urgent' THEN interval '1 hour'
                    WHEN 'high' THEN interval '4 hours'
                    WHEN 'normal' THEN interval '8 hours'
                    ELSE interval '24 hours'
                END
            ),
            resolution_due_at = COALESCE(
                resolution_due_at,
                created_at + CASE priority::text
                    WHEN 'urgent' THEN interval '8 hours'
                    WHEN 'high' THEN interval '24 hours'
                    WHEN 'normal' THEN interval '72 hours'
                    ELSE interval '7 days'
                END
            ),
            solved_at = CASE
                WHEN solved_at IS NULL AND status::text = 'solved' THEN updated_at
                ELSE solved_at
            END
        """
    )


def downgrade() -> None:
    columns = {item["name"] for item in inspect(op.get_bind()).get_columns("ticket_history")}
    if "event_type" in columns:
        indexes = {item["name"] for item in inspect(op.get_bind()).get_indexes("ticket_history")}
        if op.f("ix_ticket_history_event_type") in indexes:
            op.drop_index(op.f("ix_ticket_history_event_type"), table_name="ticket_history")
        op.drop_column("ticket_history", "event_type")
    if "event_metadata" in columns:
        op.drop_column("ticket_history", "event_metadata")

    ticket_columns = {item["name"] for item in inspect(op.get_bind()).get_columns("tickets")}
    for column_name in ["solved_at", "first_response_at", "resolution_due_at", "first_response_due_at"]:
        if column_name in ticket_columns:
            op.drop_column("tickets", column_name)
