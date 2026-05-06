"""add support submission fields

Revision ID: 0003_support_fields
Revises: 0002_user_is_active
Create Date: 2026-05-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0003_support_fields"
down_revision: Union[str, None] = "0002_user_is_active"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("tickets")}
    if "requester_email" not in columns:
        op.add_column("tickets", sa.Column("requester_email", sa.String(length=255), nullable=True))
        op.create_index(op.f("ix_tickets_requester_email"), "tickets", ["requester_email"], unique=False)
    if "company" not in columns:
        op.add_column("tickets", sa.Column("company", sa.String(length=255), nullable=True))
    if "store" not in columns:
        op.add_column("tickets", sa.Column("store", sa.String(length=255), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("tickets")}
    if "requester_email" in columns:
        op.drop_index(op.f("ix_tickets_requester_email"), table_name="tickets")
        op.drop_column("tickets", "requester_email")
    if "store" in columns:
        op.drop_column("tickets", "store")
    if "company" in columns:
        op.drop_column("tickets", "company")
