"""add participant_user_ids to session_suggestions

Revision ID: 20260404_0002
Revises: 20260314_0001
Create Date: 2026-04-04 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0002"
down_revision = "20260314_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_suggestions",
        sa.Column("participant_user_ids", sa.JSON(), nullable=True),
    )
    op.execute(
        """
        UPDATE session_suggestions
        SET participant_user_ids = json_build_array(mentor_user_id, learner_user_id)
        """
    )
    op.alter_column("session_suggestions", "participant_user_ids", nullable=False)


def downgrade() -> None:
    op.drop_column("session_suggestions", "participant_user_ids")
