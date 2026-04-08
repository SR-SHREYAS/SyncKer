"""add collaboration_title to session_suggestions

Revision ID: 20260404_0003
Revises: 20260404_0002
Create Date: 2026-04-04 00:30:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260404_0003"
down_revision = "20260404_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_suggestions",
        sa.Column("collaboration_title", sa.String(length=180), nullable=True),
    )
    op.execute("""
        UPDATE session_suggestions
        SET collaboration_title = 'Collaboration Session'
        """)
    op.alter_column("session_suggestions", "collaboration_title", nullable=False)


def downgrade() -> None:
    op.drop_column("session_suggestions", "collaboration_title")
