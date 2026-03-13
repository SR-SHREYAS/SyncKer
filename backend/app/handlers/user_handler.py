"""User request handlers."""

from app.core.exceptions import NotFoundError
from app.schemas.profile import ProfileCreateRequest, ProfileResponse, ProfileUpdateRequest
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService


class UserHandler:
    """Maps user-related requests to user service calls."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    def get_me(self, user_id: int) -> UserResponse:
        """Return the current user's main account fields."""
        result = self.user_service.get_user_details(user_id)
        return UserResponse.model_validate(result.user)

    def update_me(self, user_id: int, payload: UserUpdateRequest) -> UserResponse:
        """Update current-user account fields."""
        result = self.user_service.update_user(
            user_id,
            username=payload.username,
        )
        return UserResponse.model_validate(result.user)

    def get_profile(self, user_id: int) -> ProfileResponse:
        """Return the current user's profile."""
        result = self.user_service.get_user_details(user_id)
        if result.profile is None:
            raise NotFoundError("profile not found")
        return ProfileResponse.model_validate(result.profile)

    def create_profile(self, user_id: int, payload: ProfileCreateRequest) -> ProfileResponse:
        """Create the current user's profile."""
        profile = self.user_service.create_profile(
            user_id,
            full_name=payload.full_name,
            bio=payload.bio,
            role=payload.role,
            timezone=payload.timezone,
        )
        return ProfileResponse.model_validate(profile)

    def update_profile(self, user_id: int, payload: ProfileUpdateRequest) -> ProfileResponse:
        """Update the current user's profile."""
        profile = self.user_service.update_profile(
            user_id,
            full_name=payload.full_name,
            bio=payload.bio,
            role=payload.role,
            timezone=payload.timezone,
        )
        return ProfileResponse.model_validate(profile)
