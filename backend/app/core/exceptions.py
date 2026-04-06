"""Shared application exceptions."""


class AppError(Exception):
    """Base application error used for controlled service failures."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConflictError(AppError):
    """Raised when a record already exists and cannot be duplicated."""

    status_code = 409


class BadRequestError(AppError):
    """Raised when request content is empty or semantically invalid."""

    status_code = 400


class AuthenticationError(AppError):
    """Raised when login credentials or auth state are invalid."""

    status_code = 401


class ForbiddenError(AppError):
    """Raised when user is authenticated but not allowed to perform an action."""

    status_code = 403


class InternalServerError(AppError):
    """Raised when internal application state is inconsistent."""

    status_code = 500


class NotFoundError(AppError):
    """Raised when a requested record does not exist."""

    status_code = 404
