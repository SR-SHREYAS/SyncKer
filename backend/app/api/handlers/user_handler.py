"""User request handlers."""

from app.core.exceptions import AppError, NotFoundError
from app.schemas.profile import ProfileCreateRequest, ProfileResponse, ProfileUpdateRequest
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.logger import get_logger
from app.utils.request_validation import (
    ensure_non_empty_text,
    ensure_payload_has_updates,
    ensure_positive_id,
)

logger = get_logger(__name__)


class UserHandler:
    """Maps user-related requests to user service calls."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    def getCurrentUser(self, user_id: int) -> UserResponse:
        """Return the current user's main account fields."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            result = self.user_service.GetCurrentUserDetails(user_id)
            response = UserResponse.model_validate(result.user)
            logger.info("user getCurrentUser handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user getCurrentUser failed for user_id=%s", user_id)
            raise

    def updateCurrentUser(self, user_id: int, payload: UserUpdateRequest) -> UserResponse:
        """Update current-user account fields."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_payload_has_updates(payload, field_names=("username",))
            if payload.username is not None:
                ensure_non_empty_text(payload.username, field_name="username")

            result = self.user_service.UpdateCurrentUser(
                user_id,
                username=payload.username,
            )
            response = UserResponse.model_validate(result.user)
            logger.info("user updateCurrentUser handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user updateCurrentUser failed for user_id=%s", user_id)
            raise

    def getCurrentUserProfile(self, user_id: int) -> ProfileResponse:
        """Return the current user's profile."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            result = self.user_service.GetCurrentUserDetails(user_id)
            if result.profile is None:
                raise NotFoundError("profile not found")
            response = ProfileResponse.model_validate(result.profile)
            logger.info("user getCurrentUserProfile handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user getCurrentUserProfile failed for user_id=%s", user_id)
            raise

    def createCurrentUserProfile(self, user_id: int, payload: ProfileCreateRequest) -> ProfileResponse:
        """Create the current user's profile."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_non_empty_text(payload.full_name, field_name="full_name")
            ensure_non_empty_text(payload.timezone, field_name="timezone")

            profile = self.user_service.CreateCurrentUserProfile(
                user_id,
                full_name=payload.full_name,
                bio=payload.bio,
                role=payload.role,
                timezone=payload.timezone,
            )
            response = ProfileResponse.model_validate(profile)
            logger.info("user createCurrentUserProfile handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user createCurrentUserProfile failed for user_id=%s", user_id)
            raise

    def updateCurrentUserProfile(self, user_id: int, payload: ProfileUpdateRequest) -> ProfileResponse:
        """Update the current user's profile."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_payload_has_updates(
                payload,
                field_names=("full_name", "bio", "role", "timezone"),
            )
            if payload.full_name is not None:
                ensure_non_empty_text(payload.full_name, field_name="full_name")
            if payload.timezone is not None:
                ensure_non_empty_text(payload.timezone, field_name="timezone")

            profile = self.user_service.UpdateCurrentUserProfile(
                user_id,
                full_name=payload.full_name,
                bio=payload.bio,
                role=payload.role,
                timezone=payload.timezone,
            )
            response = ProfileResponse.model_validate(profile)
            logger.info("user updateCurrentUserProfile handled for user_id=%s", user_id)
            return response
        except AppError:
            logger.exception("user updateCurrentUserProfile failed for user_id=%s", user_id)
            raise
