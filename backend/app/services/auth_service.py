"""Authentication business logic."""

from dataclasses import dataclass
from datetime import datetime

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class AuthResult:
    """Auth output returned after a successful login or registration."""

    user: User
    access_token: str
    expires_at: datetime


class AuthService:
    """Business rules for registering and authenticating users."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    def RegisterUser(self, *, email: str, username: str, password: str) -> AuthResult:
        """Create a user account, then issue an access token."""
        if self.user_repo.get_by_email(email):
            logger.error("auth register blocked: email already exists for email=%s", email)
            raise ConflictError("email is already registered")

        if self.user_repo.get_by_username(username):
            logger.error("auth register blocked: username already exists for username=%s", username)
            raise ConflictError("username is already taken")

        password_hash = hash_password(password)
        user = self.user_repo.create_user(
            email=email,
            username=username,
            password_hash=password_hash,
        )
        access_token, expires_at = create_access_token(user.id)
        logger.info("auth register service completed for user_id=%s", user.id)
        return AuthResult(user=user, access_token=access_token, expires_at=expires_at)

    def LoginUser(self, *, email: str, password: str) -> AuthResult:
        """Verify credentials, then issue an access token."""
        user = self.user_repo.get_by_email(email)
        if user is None:
            logger.error("auth login blocked: user not found for email=%s", email)
            raise AuthenticationError("invalid email or password")

        if not user.is_active:
            logger.error("auth login blocked: inactive account for user_id=%s", user.id)
            raise AuthenticationError("user account is inactive")

        if not verify_password(password, user.password_hash):
            logger.error("auth login blocked: password mismatch for user_id=%s", user.id)
            raise AuthenticationError("invalid email or password")

        access_token, expires_at = create_access_token(user.id)
        logger.info("auth login service completed for user_id=%s", user.id)
        return AuthResult(user=user, access_token=access_token, expires_at=expires_at)
