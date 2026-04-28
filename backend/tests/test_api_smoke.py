from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import AppError
from app.main import app, create_app, health_check


def test_app_imports_with_expected_title() -> None:
    assert app.title == Settings(_env_file=None).app_name


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


def test_create_app_registers_health_route() -> None:
    test_app = create_app()

    health_routes = [route for route in test_app.routes if route.path == "/health"]

    assert len(health_routes) == 1
    assert health_routes[0].endpoint is health_check


def test_create_app_registers_exception_handlers() -> None:
    test_app = create_app()

    assert AppError in test_app.exception_handlers
    assert Exception in test_app.exception_handlers


def test_create_app_includes_cors_middleware_for_configured_origins(
    monkeypatch,
) -> None:
    allowed_origins = ["http://localhost:5173", "https://syncskill.app"]
    monkeypatch.setattr("app.main.settings.cors_allowed_origins", allowed_origins)

    test_app = create_app()

    cors_middlewares = [
        middleware
        for middleware in test_app.user_middleware
        if middleware.cls is CORSMiddleware
    ]

    assert len(cors_middlewares) == 1

    cors_middleware = cors_middlewares[0]
    assert cors_middleware.kwargs["allow_origins"] == allowed_origins
    assert cors_middleware.kwargs["allow_credentials"] is False
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


def test_settings_parse_json_list_cors_origins() -> None:
    settings = Settings(
        _env_file=None,
        cors_allowed_origins='["http://localhost:5173", "https://syncskill.app"]',
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "https://syncskill.app",
    ]


def test_settings_parse_none_cors_origins_as_empty_list() -> None:
    settings = Settings(_env_file=None, cors_allowed_origins=None)

    assert settings.cors_allowed_origins == []


def test_settings_parse_blank_cors_origins_as_empty_list() -> None:
    settings = Settings(_env_file=None, cors_allowed_origins="  ")

    assert settings.cors_allowed_origins == []


def test_settings_reject_invalid_json_cors_origins() -> None:
    try:
        Settings(_env_file=None, cors_allowed_origins='["http://localhost:5173"')
    except ValidationError as exc:
        assert "valid JSON array or comma-separated string" in str(exc)
    else:
        raise AssertionError("expected invalid JSON CORS config to fail validation")


def test_settings_reject_non_list_json_cors_origins() -> None:
    try:
        Settings(_env_file=None, cors_allowed_origins='{"origin": "http://localhost:5173"}')
    except ValidationError as exc:
        assert "must decode to a list" in str(exc)
    else:
        raise AssertionError("expected non-list JSON CORS config to fail validation")
