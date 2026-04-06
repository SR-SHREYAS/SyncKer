"""add team workspace core

Revision ID: 20260405_0004
Revises: 20260404_0003
Create Date: 2026-04-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0004"
down_revision = "20260404_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        op.f("ix_teams_owner_user_id"), "teams", ["owner_user_id"], unique=False
    )

    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_member"),
    )
    op.create_index(
        op.f("ix_team_members_team_id"), "team_members", ["team_id"], unique=False
    )
    op.create_index(
        op.f("ix_team_members_user_id"), "team_members", ["user_id"], unique=False
    )

    op.add_column(
        "session_suggestions", sa.Column("team_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f("ix_session_suggestions_team_id"),
        "session_suggestions",
        ["team_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_session_suggestions_team_id_teams",
        "session_suggestions",
        "teams",
        ["team_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_session_suggestions_team_id_teams",
        "session_suggestions",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_session_suggestions_team_id"), table_name="session_suggestions"
    )
    op.drop_column("session_suggestions", "team_id")

    op.drop_index(op.f("ix_team_members_user_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_team_id"), table_name="team_members")
    op.drop_table("team_members")

    op.drop_index(op.f("ix_teams_owner_user_id"), table_name="teams")
    op.drop_table("teams")
