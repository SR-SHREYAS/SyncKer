"""initial schema

Revision ID: 20260314_0001
Revises:
Create Date: 2026-03-14 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260314_0001"
down_revision = None
branch_labels = None
depends_on = None


profile_role = sa.Enum("learner", "mentor", "both", name="profile_role")
proficiency_level = sa.Enum("beginner", "intermediate", "advanced", name="proficiency_level")
task_priority = sa.Enum("low", "medium", "high", name="task_priority")
task_status = sa.Enum("pending", "in_progress", "completed", name="task_status")
suggestion_status = sa.Enum("pending", "accepted", "rejected", "expired", name="suggestion_status")
session_status = sa.Enum("scheduled", "completed", "cancelled", name="session_status")
participant_role = sa.Enum("mentor", "learner", name="participant_role")
participant_response_status = sa.Enum(
    "invited",
    "accepted",
    "declined",
    name="participant_response_status",
)


def upgrade() -> None:
    profile_role.create(op.get_bind(), checkfirst=True)
    proficiency_level.create(op.get_bind(), checkfirst=True)
    task_priority.create(op.get_bind(), checkfirst=True)
    task_status.create(op.get_bind(), checkfirst=True)
    suggestion_status.create(op.get_bind(), checkfirst=True)
    session_status.create(op.get_bind(), checkfirst=True)
    participant_role.create(op.get_bind(), checkfirst=True)
    participant_response_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_skills_slug"), "skills", ["slug"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("role", profile_role, nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "user_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("proficiency_level", proficiency_level, nullable=False),
        sa.Column("is_teaching", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_learning", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", task_priority, nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"], unique=False)

    op.create_table(
        "availability_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("specific_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_availability_blocks_user_id"), "availability_blocks", ["user_id"], unique=False)

    op.create_table(
        "routine_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("specific_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_routine_blocks_user_id"), "routine_blocks", ["user_id"], unique=False)

    op.create_table(
        "session_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("generated_for_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mentor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("learner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("suggested_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suggested_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("status", suggestion_status, nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_suggestion_id", sa.Integer(), sa.ForeignKey("session_suggestions.id"), nullable=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", session_status, nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_suggestion_id"),
    )

    op.create_table(
        "session_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("participant_role", participant_role, nullable=False),
        sa.Column("response_status", participant_response_status, nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "user_id", name="uq_session_participant"),
    )


def downgrade() -> None:
    op.drop_table("session_participants")
    op.drop_table("sessions")
    op.drop_table("session_suggestions")
    op.drop_index(op.f("ix_routine_blocks_user_id"), table_name="routine_blocks")
    op.drop_table("routine_blocks")
    op.drop_index(op.f("ix_availability_blocks_user_id"), table_name="availability_blocks")
    op.drop_table("availability_blocks")
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("user_skills")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_skills_slug"), table_name="skills")
    op.drop_table("skills")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    participant_response_status.drop(op.get_bind(), checkfirst=True)
    participant_role.drop(op.get_bind(), checkfirst=True)
    session_status.drop(op.get_bind(), checkfirst=True)
    suggestion_status.drop(op.get_bind(), checkfirst=True)
    task_status.drop(op.get_bind(), checkfirst=True)
    task_priority.drop(op.get_bind(), checkfirst=True)
    proficiency_level.drop(op.get_bind(), checkfirst=True)
    profile_role.drop(op.get_bind(), checkfirst=True)
