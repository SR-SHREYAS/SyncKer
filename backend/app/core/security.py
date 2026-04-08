"""Password and token helpers."""

from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import os
from typing import Any

import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a password before storing it in the database.

    We never store raw passwords. Only the derived hash is saved.
    """
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    salt_text = base64.b64encode(salt).decode("utf-8")
    hash_text = base64.b64encode(hashed).decode("utf-8")
    return f"{salt_text}:{hash_text}"


def verify_password(password: str, password_hash: str) -> bool:
    """Compare a plain password with the stored password hash."""
    try:
        salt_text, hash_text = password_hash.split(":", maxsplit=1)
    except ValueError:
        return False

    salt = base64.b64decode(salt_text.encode("utf-8"))
    expected_hash = base64.b64decode(hash_text.encode("utf-8"))
    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 100_000
    )
    return hmac.compare_digest(candidate_hash, expected_hash)


def create_access_token(
    subject: str | int, expires_delta: timedelta | None = None
) -> tuple[str, datetime]:
    """Create a signed JWT access token for one authenticated user."""
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a signed JWT access token."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
