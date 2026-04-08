"""User business logic."""

from dataclasses import dataclass

from app.core.exceptions import ConflictError, NotFoundError
from app.models.profile import Profile
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class UserDetailsResult:
    """Combined user view used by the handler layer."""

    user: User
    profile: Profile | None


class UserService:
    """Business rules for user and profile operations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    def GetCurrentUserDetails(self, user_id: int) -> UserDetailsResult:
        """Return one user with its profile data."""
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            logger.error("user details blocked: user not found")
            raise NotFoundError("user not found")
        logger.info("user details service completed")
        return UserDetailsResult(user=user, profile=user.profile)

    def UpdateCurrentUser(
        self, user_id: int, *, username: str | None = None
    ) -> UserDetailsResult:
        """Update allowed user fields after validation."""
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            logger.error("user update blocked: user not found")
            raise NotFoundError("user not found")

        updates: dict[str, object] = {}
        if username is not None and username != user.username:
            existing_user = self.user_repo.get_by_username(username)
            if existing_user is not None and existing_user.id != user_id:
                logger.error("user update blocked: username already exists")
                raise ConflictError("username is already taken")
            updates["username"] = username

        if updates:
            user = self.user_repo.update_user(user, **updates)

        logger.info("user update service completed")
        return UserDetailsResult(user=user, profile=user.profile)

    def CreateCurrentUserProfile(
        self, user_id: int, *, full_name: str, bio: str | None, role: str, timezone: str
    ) -> Profile:
        """Create the profile for one existing user."""
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            logger.error("profile create blocked: user not found")
            raise NotFoundError("user not found")

        existing_profile = self.user_repo.get_profile_by_user_id(user_id)
        if existing_profile is not None:
            logger.error("profile create blocked: profile already exists")
            raise ConflictError("profile already exists")

        profile = self.user_repo.create_profile(
            user_id=user_id,
            full_name=full_name,
            bio=bio,
            role=role,
            timezone=timezone,
        )
        logger.info("profile create service completed")
        return profile

    def UpdateCurrentUserProfile(
        self,
        user_id: int,
        *,
        full_name: str | None = None,
        bio: str | None = None,
        role: str | None = None,
        timezone: str | None = None
    ) -> Profile:
        """Update profile fields for one existing user."""
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            logger.error("profile update blocked: user not found")
            raise NotFoundError("user not found")

        profile = self.user_repo.get_profile_by_user_id(user_id)
        if profile is None:
            logger.error("profile update blocked: profile not found")
            raise NotFoundError("profile not found")

        updates: dict[str, object] = {}
        if full_name is not None:
            updates["full_name"] = full_name
        if bio is not None:
            updates["bio"] = bio
        if role is not None:
            updates["role"] = role
        if timezone is not None:
            updates["timezone"] = timezone

        if updates:
            profile = self.user_repo.update_profile(profile, **updates)

        logger.info("profile update service completed")
        return profile
