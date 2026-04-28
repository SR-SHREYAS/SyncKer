from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.main import app, create_app, health_check


def test_app_imports_with_expected_title() -> None:
    assert app.title == "SyncSkill"


def test_health_check_returns_ok() -> None:
    assert health_check() == {"status": "ok"}


def test_create_app_has_no_cors_middleware_when_origins_are_empty(
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.main.settings.cors_allowed_origins", [])

    test_app = create_app()

    assert all(
        middleware.cls is not CORSMiddleware for middleware in test_app.user_middleware
    )


def test_create_app_includes_cors_middleware_for_configured_origins(
    monkeypatch,
) -> None:
    allowed_origins = ["http://localhost:5173", "https://syncskill.app"]
    monkeypatch.setattr("app.main.settings.cors_allowed_origins", allowed_origins)

    test_app = create_app()

    cors_middleware = next(
        (
            middleware
            for middleware in test_app.user_middleware
            if middleware.cls is CORSMiddleware
        ),
        None,
    )
    assert cors_middleware is not None
    assert cors_middleware.kwargs["allow_origins"] == allowed_origins
    assert cors_middleware.kwargs["allow_methods"] == ["*"]
    assert cors_middleware.kwargs["allow_headers"] == ["*"]


def test_settings_parse_comma_separated_cors_origins() -> None:
    settings = Settings(
        _env_file=None,
        cors_allowed_origins="http://localhost:5173, https://syncskill.app",
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "https://syncskill.app",
    ]


def test_settings_parse_blank_cors_origins_as_empty_list() -> None:
    settings = Settings(_env_file=None, cors_allowed_origins="  ")

    assert settings.cors_allowed_origins == []
