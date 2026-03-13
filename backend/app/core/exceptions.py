"""Shared application exceptions."""


class AppError(Exception):
    """Base application error used for controlled service failures."""


class ConflictError(AppError):
    """Raised when a record already exists and cannot be duplicated."""


class AuthenticationError(AppError):
    """Raised when login credentials or auth state are invalid."""


class NotFoundError(AppError):
    """Raised when a requested record does not exist."""
