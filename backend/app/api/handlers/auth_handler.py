"""Auth request handlers."""

from app.core.exceptions import AppError
from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthHandler:
    """Maps auth requests to auth service calls."""

    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    def registerUser(self, payload: RegisterRequest) -> AuthResponse:
        """Handle registration input and shape the auth response."""
        try:
            # Call service layer.
            auth_result = self.auth_service.RegisterUser(
                email=payload.email,
                username=payload.username,
                password=payload.password,
            )

            # Build response model.
            auth_response = self._build_auth_response(
                auth_result.user,
                auth_result.access_token,
                auth_result.expires_at,
            )
            logger.info("auth register handler completed")
            return auth_response
        except AppError:
            logger.exception("auth register handler failed")
            raise

    def loginUser(self, payload: LoginRequest) -> AuthResponse:
        """Handle login input and shape the auth response."""
        try:
            # Call service layer.
            auth_result = self.auth_service.LoginUser(
                email=payload.email,
                password=payload.password,
            )

            # Build response model.
            auth_response = self._build_auth_response(
                auth_result.user,
                auth_result.access_token,
                auth_result.expires_at,
            )
            logger.info("auth login handler completed")
            return auth_response
        except AppError:
            logger.exception("auth login handler failed")
            raise

    def _build_auth_response(self, user: object, access_token: str, expires_at: object) -> AuthResponse:
        """Keep auth response mapping in one place for both flows."""
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            token=TokenResponse(
                access_token=access_token,
                expires_at=expires_at,
            ),
        )
