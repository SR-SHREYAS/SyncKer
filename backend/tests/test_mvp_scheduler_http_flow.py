"""HTTP-level MVP scheduler smoke flow tests."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
import os
import socket
import subprocess
import sys
import time

import httpx
import pytest
from sqlalchemy import create_engine

from app.db.base import Base

# Import all model modules so relationship-based mappers are fully registered.
from app.models.availability_block import AvailabilityBlock  # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.routine_block import RoutineBlock  # noqa: F401
from app.models.session import Session as SessionModel  # noqa: F401
from app.models.session_participant import SessionParticipant  # noqa: F401
from app.models.session_suggestion import SessionSuggestion  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.team_member import TeamMember  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_skill import UserSkill  # noqa: F401


def _find_free_port() -> int:
    """Return one available local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
        temp_socket.bind(("127.0.0.1", 0))
        return int(temp_socket.getsockname()[1])


def _wait_for_server(base_url: str, *, process: subprocess.Popen[str]) -> None:
    """Wait until the local API process responds to health checks."""
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = ""
            if process.stdout is not None:
                output = process.stdout.read()
            raise RuntimeError(
                "Uvicorn process exited before readiness check. " f"Output: {output}"
            )
        try:
            response = httpx.get(f"{base_url}/health", timeout=0.5)
            if response.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("Uvicorn process did not become ready in time")


@pytest.fixture(scope="module")
def api_base_url(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str, None, None]:
    """Run local Uvicorn server bound to an isolated SQLite database."""
    backend_dir = Path(__file__).resolve().parents[1]
    temp_dir = tmp_path_factory.mktemp("mvp_http_flow")
    database_path = temp_dir / "mvp_http_flow.db"
    database_url = f"sqlite+pysqlite:///{database_path}"

    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["JWT_SECRET_KEY"] = "test-secret-key-for-http-flow-tests"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(backend_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_for_server(base_url, process=process)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

        drop_engine = create_engine(database_url, future=True)
        Base.metadata.drop_all(bind=drop_engine)
        drop_engine.dispose()


@pytest.fixture
def api_client(api_base_url: str) -> Generator[httpx.Client, None, None]:
    """Provide HTTP client for local API process."""
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        yield client


def _register_user(
    client: httpx.Client,
    *,
    email: str,
    username: str,
    password: str = "StrongPass123",
) -> dict:
    """Register one user and return response JSON."""
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 201
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    """Build bearer auth headers for API calls."""
    return {"Authorization": f"Bearer {access_token}"}


def test_mvp_scheduler_http_flow_end_to_end(api_client: httpx.Client) -> None:
    """Cover core HTTP flow from auth to applied suggestion and timetable read."""
    owner_auth = _register_user(
        api_client,
        email="owner-http@example.com",
        username="owner_http",
    )
    participant_auth = _register_user(
        api_client,
        email="participant-http@example.com",
        username="participant_http",
    )
    owner_id = owner_auth["user"]["id"]
    participant_id = participant_auth["user"]["id"]
    owner_headers = _auth_headers(owner_auth["token"]["access_token"])
    participant_headers = _auth_headers(participant_auth["token"]["access_token"])

    create_team_response = api_client.post(
        "/teams",
        headers=owner_headers,
        json={
            "name": "HTTP Alpha Team",
            "description": "MVP http smoke team",
        },
    )
    assert create_team_response.status_code == 201
    created_team_id = create_team_response.json()["id"]

    add_member_response = api_client.post(
        f"/teams/{created_team_id}/members",
        headers=owner_headers,
        json={"participant_user_id": participant_id},
    )
    assert add_member_response.status_code == 201

    current_time = datetime.now(UTC).replace(second=0, microsecond=0)
    create_owner_task_response = api_client.post(
        "/planning/tasks",
        headers=owner_headers,
        json={
            "title": "Owner focus task",
            "description": "Owner work",
            "priority": "medium",
            "status": "pending",
            "estimated_minutes": 45,
            "deadline_at": None,
            "planned_start_at": (current_time + timedelta(minutes=30)).isoformat(),
            "planned_end_at": (current_time + timedelta(minutes=90)).isoformat(),
            "skill_id": None,
        },
    )
    assert create_owner_task_response.status_code == 201

    create_participant_task_response = api_client.post(
        "/planning/tasks",
        headers=participant_headers,
        json={
            "title": "Participant focus task",
            "description": "Participant work",
            "priority": "medium",
            "status": "pending",
            "estimated_minutes": 45,
            "deadline_at": None,
            "planned_start_at": (current_time + timedelta(minutes=20)).isoformat(),
            "planned_end_at": (current_time + timedelta(minutes=80)).isoformat(),
            "skill_id": None,
        },
    )
    assert create_participant_task_response.status_code == 201

    generate_response = api_client.post(
        "/scheduling/suggestions/generate",
        headers=owner_headers,
        json={
            "team_id": created_team_id,
            "participant_user_ids": [owner_id, participant_id],
            "collaboration_title": "MVP collaboration block",
            "skill_id": None,
            "window_start_at": current_time.isoformat(),
            "window_end_at": (current_time + timedelta(hours=4)).isoformat(),
            "minimum_duration_minutes": 30,
        },
    )
    assert generate_response.status_code == 201
    generated_suggestion = generate_response.json()
    assert generated_suggestion["status"] == "pending"

    apply_response = api_client.post(
        f"/scheduling/suggestions/{generated_suggestion['id']}/apply",
        headers=owner_headers,
    )
    assert apply_response.status_code == 200
    applied_suggestion = apply_response.json()
    assert applied_suggestion["status"] == "accepted"

    owner_tasks_response = api_client.get("/planning/tasks", headers=owner_headers)
    assert owner_tasks_response.status_code == 200
    owner_tasks = owner_tasks_response.json()
    assert any(
        item["title"] == generated_suggestion["collaboration_title"]
        for item in owner_tasks
    )

    timetable_response = api_client.get(
        f"/planning/teams/{created_team_id}/timetable",
        headers=owner_headers,
    )
    assert timetable_response.status_code == 200
    team_timetable = timetable_response.json()
    assert team_timetable["team_id"] == created_team_id
    participant_ids = {item["user_id"] for item in team_timetable["participants"]}
    assert participant_ids == {owner_id, participant_id}
    assert all(
        any(
            task_item["title"] == generated_suggestion["collaboration_title"]
            for task_item in participant_row["tasks"]
        )
        for participant_row in team_timetable["participants"]
    )


def test_http_invalid_token_is_rejected(api_client: httpx.Client) -> None:
    """Reject malformed bearer token with 401 response."""
    response = api_client.get(
        "/teams",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid or expired access token"}


def test_http_team_timetable_rejects_non_member_user(api_client: httpx.Client) -> None:
    """Reject team timetable read for user outside team membership."""
    owner_auth = _register_user(
        api_client,
        email="team-owner-http@example.com",
        username="team_owner_http",
    )
    member_auth = _register_user(
        api_client,
        email="team-member-http@example.com",
        username="team_member_http",
    )
    outsider_auth = _register_user(
        api_client,
        email="team-outsider-http@example.com",
        username="team_outsider_http",
    )
    owner_headers = _auth_headers(owner_auth["token"]["access_token"])
    outsider_headers = _auth_headers(outsider_auth["token"]["access_token"])

    create_team_response = api_client.post(
        "/teams",
        headers=owner_headers,
        json={
            "name": "Restricted Team HTTP",
            "description": "Only members can read timetable",
        },
    )
    assert create_team_response.status_code == 201
    created_team_id = create_team_response.json()["id"]

    add_member_response = api_client.post(
        f"/teams/{created_team_id}/members",
        headers=owner_headers,
        json={"participant_user_id": member_auth["user"]["id"]},
    )
    assert add_member_response.status_code == 201

    outsider_timetable_response = api_client.get(
        f"/planning/teams/{created_team_id}/timetable",
        headers=outsider_headers,
    )
    assert outsider_timetable_response.status_code == 403
    assert outsider_timetable_response.json() == {
        "detail": "user is not a member of this team"
    }


def test_http_apply_suggestion_rejects_non_pending_status(
    api_client: httpx.Client,
) -> None:
    """Reject apply when suggestion status is already non-pending."""
    owner_auth = _register_user(
        api_client,
        email="status-owner-http@example.com",
        username="status_owner_http",
    )
    participant_auth = _register_user(
        api_client,
        email="status-participant-http@example.com",
        username="status_participant_http",
    )
    owner_id = owner_auth["user"]["id"]
    participant_id = participant_auth["user"]["id"]
    owner_headers = _auth_headers(owner_auth["token"]["access_token"])

    create_team_response = api_client.post(
        "/teams",
        headers=owner_headers,
        json={
            "name": "Status Team HTTP",
            "description": "Apply state validation team",
        },
    )
    assert create_team_response.status_code == 201
    created_team_id = create_team_response.json()["id"]

    add_member_response = api_client.post(
        f"/teams/{created_team_id}/members",
        headers=owner_headers,
        json={"participant_user_id": participant_id},
    )
    assert add_member_response.status_code == 201

    current_time = datetime.now(UTC).replace(second=0, microsecond=0)
    generate_response = api_client.post(
        "/scheduling/suggestions/generate",
        headers=owner_headers,
        json={
            "team_id": created_team_id,
            "participant_user_ids": [owner_id, participant_id],
            "collaboration_title": "Reject then apply",
            "skill_id": None,
            "window_start_at": current_time.isoformat(),
            "window_end_at": (current_time + timedelta(hours=2)).isoformat(),
            "minimum_duration_minutes": 30,
        },
    )
    assert generate_response.status_code == 201
    generated_suggestion_id = generate_response.json()["id"]

    reject_response = api_client.patch(
        f"/scheduling/suggestions/{generated_suggestion_id}",
        headers=owner_headers,
        json={"status": "rejected"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    apply_response = api_client.post(
        f"/scheduling/suggestions/{generated_suggestion_id}/apply",
        headers=owner_headers,
    )
    assert apply_response.status_code == 409
    assert apply_response.json() == {
        "detail": "only pending suggestions can be applied"
    }
