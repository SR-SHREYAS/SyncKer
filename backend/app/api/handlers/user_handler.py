"""User request handlers."""

from app.core.exceptions import AppError, NotFoundError
from app.schemas.profile import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.logger import get_logger
from app.utils.request_validation import (
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
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")

            # Call service layer.
            user_details = self.user_service.GetCurrentUserDetails(user_id)
            user_response = UserResponse.model_validate(user_details.user)
            logger.info("user get current user handler completed")
            return user_response
        except AppError:
            logger.exception("user get current user handler failed")
            raise

    def updateCurrentUser(
        self, user_id: int, payload: UserUpdateRequest
    ) -> UserResponse:
        """Update current-user account fields."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")
            ensure_payload_has_updates(payload, field_names=("username",))

            # Call service layer.
            updated_user_details = self.user_service.UpdateCurrentUser(
                user_id,
                username=payload.username,
            )
            user_response = UserResponse.model_validate(updated_user_details.user)
            logger.info("user update current user handler completed")
            return user_response
        except AppError:
            logger.exception("user update current user handler failed")
            raise

    def getCurrentUserProfile(self, user_id: int) -> ProfileResponse:
        """Return the current user's profile."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")

            # Call service layer.
            user_details = self.user_service.GetCurrentUserDetails(user_id)
            if user_details.profile is None:
                raise NotFoundError("profile not found")
            profile_response = ProfileResponse.model_validate(user_details.profile)
            logger.info("user get current user profile handler completed")
            return profile_response
        except AppError:
            logger.exception("user get current user profile handler failed")
            raise

    def createCurrentUserProfile(
        self, user_id: int, payload: ProfileCreateRequest
    ) -> ProfileResponse:
        """Create the current user's profile."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")

            # Call service layer.
            profile = self.user_service.CreateCurrentUserProfile(
                user_id,
                full_name=payload.full_name,
                bio=payload.bio,
                role=payload.role,
                timezone=payload.timezone,
            )
            profile_response = ProfileResponse.model_validate(profile)
            logger.info("user create current user profile handler completed")
            return profile_response
        except AppError:
            logger.exception("user create current user profile handler failed")
            raise

    def updateCurrentUserProfile(
        self, user_id: int, payload: ProfileUpdateRequest
    ) -> ProfileResponse:
        """Update the current user's profile."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")
            ensure_payload_has_updates(
                payload,
                field_names=("full_name", "bio", "role", "timezone"),
            )

            # Call service layer.
            updated_profile = self.user_service.UpdateCurrentUserProfile(
                user_id,
                full_name=payload.full_name,
                bio=payload.bio,
                role=payload.role,
                timezone=payload.timezone,
            )
            profile_response = ProfileResponse.model_validate(updated_profile)
            logger.info("user update current user profile handler completed")
            return profile_response
        except AppError:
            logger.exception("user update current user profile handler failed")
            raise
