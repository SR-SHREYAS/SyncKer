from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify_roundtrip() -> None:
    password = "super-secret-pass"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-pass", password_hash) is False


def test_access_token_roundtrip() -> None:
    token, expires_at = create_access_token(subject=123)

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert expires_at is not None
