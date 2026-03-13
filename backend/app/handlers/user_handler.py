"""User request handlers."""

from app.core.exceptions import AppError, NotFoundError
from app.schemas.profile import ProfileCreateRequest, ProfileResponse, ProfileUpdateRequest
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserHandler:
    """Maps user-related requests to user service calls."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    def get_me(self, user_id: int) -> UserResponse:
        """Return the current user's main account fields."""
        try:
            result = self.user_service.get_user_details(user_id)
            response = UserResponse.model_validate(result.user)
            logger.info("user get_me handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user get_me failed for user_id=%s", user_id)
            raise

    def update_me(self, user_id: int, payload: UserUpdateRequest) -> UserResponse:
        """Update current-user account fields."""
        try:
            result = self.user_service.update_user(
                user_id,
                username=payload.username,
            )
            response = UserResponse.model_validate(result.user)
            logger.info("user update_me handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user update_me failed for user_id=%s", user_id)
            raise

    def get_profile(self, user_id: int) -> ProfileResponse:
        """Return the current user's profile."""
        try:
            result = self.user_service.get_user_details(user_id)
            if result.profile is None:
                raise NotFoundError("profile not found")
            response = ProfileResponse.model_validate(result.profile)
            logger.info("user get_profile handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user get_profile failed for user_id=%s", user_id)
            raise

    def create_profile(self, user_id: int, payload: ProfileCreateRequest) -> ProfileResponse:
        """Create the current user's profile."""
        try:
            profile = self.user_service.create_profile(
                user_id,
                full_name=payload.full_name,
                bio=payload.bio,
                role=payload.role,
                timezone=payload.timezone,
            )
            response = ProfileResponse.model_validate(profile)
            logger.info("user create_profile handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user create_profile failed for user_id=%s", user_id)
            raise

    def update_profile(self, user_id: int, payload: ProfileUpdateRequest) -> ProfileResponse:
        """Update the current user's profile."""
        try:
            profile = self.user_service.update_profile(
                user_id,
                full_name=payload.full_name,
                bio=payload.bio,
                role=payload.role,
                timezone=payload.timezone,
            )
            response = ProfileResponse.model_validate(profile)
            logger.info("user update_profile handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user update_profile failed for user_id=%s", user_id)
            raise
