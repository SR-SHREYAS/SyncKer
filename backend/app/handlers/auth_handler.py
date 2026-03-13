"""Auth request handlers."""

from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService


class AuthHandler:
    """Maps auth requests to auth service calls."""

    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    def register(self, payload: RegisterRequest) -> AuthResponse:
        """Handle registration input and shape the auth response."""
        result = self.auth_service.register(
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
        return self._build_auth_response(result.user, result.access_token, result.expires_at)

    def login(self, payload: LoginRequest) -> AuthResponse:
        """Handle login input and shape the auth response."""
        result = self.auth_service.login(
            email=payload.email,
            password=payload.password,
        )
        return self._build_auth_response(result.user, result.access_token, result.expires_at)

    def _build_auth_response(self, user: object, access_token: str, expires_at: object) -> AuthResponse:
        """Keep auth response mapping in one place for both flows."""
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            token=TokenResponse(
                access_token=access_token,
                expires_at=expires_at,
            ),
        )
