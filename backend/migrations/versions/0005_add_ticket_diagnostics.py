"""add ticket diagnostics

Revision ID: 0005_ticket_diagnostics
Revises: 0004_ticket_lifecycle
Create Date: 2026-05-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0005_ticket_diagnostics"
down_revision: Union[str, None] = "0004_ticket_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if "ticket_diagnostics" in inspector.get_table_names():
        return

    op.create_table(
        "ticket_diagnostics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=False),
        sa.Column("playbook", sa.String(length=100), nullable=False),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("service", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticket_diagnostics_id"), "ticket_diagnostics", ["id"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_ticket_id"), "ticket_diagnostics", ["ticket_id"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_intent"), "ticket_diagnostics", ["intent"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_playbook"), "ticket_diagnostics", ["playbook"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_check_name"), "ticket_diagnostics", ["check_name"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_status"), "ticket_diagnostics", ["status"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_severity"), "ticket_diagnostics", ["severity"], unique=False)
    op.create_index(op.f("ix_ticket_diagnostics_checked_at"), "ticket_diagnostics", ["checked_at"], unique=False)


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if "ticket_diagnostics" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_ticket_diagnostics_checked_at"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_severity"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_status"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_check_name"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_playbook"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_intent"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_ticket_id"), table_name="ticket_diagnostics")
    op.drop_index(op.f("ix_ticket_diagnostics_id"), table_name="ticket_diagnostics")
    op.drop_table("ticket_diagnostics")
