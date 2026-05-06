"""add user is_active

Revision ID: 0002_user_is_active
Revises: 0001_auth_ticket_tables
Create Date: 2026-05-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0002_user_is_active"
down_revision: Union[str, None] = "0001_auth_ticket_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("users")}
    if "is_active" not in columns:
        op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("users")}
    if "is_active" in columns:
        op.drop_column("users", "is_active")
