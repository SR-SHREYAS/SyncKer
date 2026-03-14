from app.main import app, health_check


def test_app_imports_with_expected_title() -> None:
    assert app.title == "SyncSkill"


def test_health_check_returns_ok() -> None:
    assert health_check() == {"status": "ok"}
