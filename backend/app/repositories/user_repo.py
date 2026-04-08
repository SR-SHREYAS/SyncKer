"""User persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.profile import Profile
from app.models.user import User


class UserRepository:
    """Database access for user and profile records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """Fetch one user with profile and skills loaded."""
        stmt = (
            select(User)
            .options(joinedload(User.profile), joinedload(User.skills))
            .where(User.id == user_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        """Fetch one user by email for login flows."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        """Fetch one user by username when checking uniqueness."""
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_user(self, *, email: str, username: str, password_hash: str, is_active: bool = True) -> User:
        """Insert a new user row and return the saved record."""
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User, **updates: object) -> User:
        """Apply field updates to an existing user."""
        for field, value in updates.items():
            setattr(user, field, value)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_profile(self, *, user_id: int, full_name: str, bio: str | None, role: str, timezone: str) -> Profile:
        """Create the one-to-one profile attached to a user."""
        profile = Profile(
            user_id=user_id,
            full_name=full_name,
            bio=bio,
            role=role,
            timezone=timezone,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_profile_by_user_id(self, user_id: int) -> Profile | None:
        """Fetch the profile row attached to a user."""
        stmt = select(Profile).where(Profile.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_profile(self, profile: Profile, **updates: object) -> Profile:
        """Apply field updates to an existing profile."""
        for field, value in updates.items():
            setattr(profile, field, value)

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
