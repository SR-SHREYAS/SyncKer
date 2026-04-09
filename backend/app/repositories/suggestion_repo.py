"""Session suggestion persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session_suggestion import SessionSuggestion


class SuggestionRepository:
    """Database access for generated session suggestions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_suggestion(
        self,
        *,
        team_id: int | None,
        generated_for_user_id: int,
        mentor_user_id: int,
        learner_user_id: int,
        participant_user_ids: list[int],
        collaboration_title: str,
        skill_id: int,
        suggested_start_at: object,
        suggested_end_at: object,
        score: float,
        status: str,
        explanation: str,
    ) -> SessionSuggestion:
        """Insert one generated session suggestion."""
        suggestion = SessionSuggestion(
            team_id=team_id,
            generated_for_user_id=generated_for_user_id,
            mentor_user_id=mentor_user_id,
            learner_user_id=learner_user_id,
            participant_user_ids=participant_user_ids,
            collaboration_title=collaboration_title,
            skill_id=skill_id,
            suggested_start_at=suggested_start_at,
            suggested_end_at=suggested_end_at,
            score=score,
            status=status,
            explanation=explanation,
        )
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def get_suggestion_by_id(self, suggestion_id: int) -> SessionSuggestion | None:
        """Fetch one suggestion by primary key."""
        stmt = select(SessionSuggestion).where(SessionSuggestion.id == suggestion_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_suggestion_by_id_for_update(
        self, suggestion_id: int
    ) -> SessionSuggestion | None:
        """Fetch one suggestion by primary key and lock it for update."""
        stmt = (
            select(SessionSuggestion)
            .where(SessionSuggestion.id == suggestion_id)
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_suggestions_for_user(self, user_id: int) -> list[SessionSuggestion]:
        """Return suggestions generated for one user."""
        stmt = (
            select(SessionSuggestion)
            .where(SessionSuggestion.generated_for_user_id == user_id)
            .order_by(SessionSuggestion.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_suggestion(
        self,
        suggestion: SessionSuggestion,
        *,
        auto_commit: bool = True,
        **updates: object,
    ) -> SessionSuggestion:
        """Apply field updates to an existing suggestion."""
        if not auto_commit and not self._has_active_transaction():
            raise RuntimeError(
                "suggestion update with auto_commit=False requires an active transaction"
            )

        for field, value in updates.items():
            setattr(suggestion, field, value)

        self.db.add(suggestion)
        if auto_commit:
            self.db.commit()
            self.db.refresh(suggestion)
        else:
            self.db.flush()
        return suggestion

    def _has_active_transaction(self) -> bool:
        """Return True when Session currently has an active transaction."""
        return bool(self.db.in_transaction())
