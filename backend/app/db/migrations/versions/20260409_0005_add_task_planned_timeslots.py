"""add planned task timeslots

Revision ID: 20260409_0005
Revises: 20260405_0004
Create Date: 2026-04-09 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409_0005"
down_revision = "20260405_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tasks", "planned_end_at")
    op.drop_column("tasks", "planned_start_at")
