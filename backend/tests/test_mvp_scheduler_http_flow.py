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
        except httpx.RequestError:
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


def _register_auth_user(
    client: httpx.Client,
    *,
    email: str,
    username: str,
) -> tuple[dict, int, dict[str, str]]:
    """Register one user and return auth payload, user id, and auth headers."""
    auth_payload = _register_user(
        client,
        email=email,
        username=username,
    )
    user_id = auth_payload["user"]["id"]
    auth_headers = _auth_headers(auth_payload["token"]["access_token"])
    return auth_payload, user_id, auth_headers


def _create_team_workspace(
    client: httpx.Client,
    *,
    owner_headers: dict[str, str],
    name: str,
    description: str,
) -> int:
    """Create one team workspace and return its id."""
    response = client.post(
        "/teams",
        headers=owner_headers,
        json={
            "name": name,
            "description": description,
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def _add_team_participant(
    client: httpx.Client,
    *,
    owner_headers: dict[str, str],
    team_id: int,
    participant_user_id: int,
) -> None:
    """Add one participant user to a team workspace."""
    response = client.post(
        f"/teams/{team_id}/members",
        headers=owner_headers,
        json={"participant_user_id": participant_user_id},
    )
    assert response.status_code == 201


def _create_planning_task(
    client: httpx.Client,
    *,
    headers: dict[str, str],
    title: str,
    description: str,
    planned_start_at: datetime,
    planned_end_at: datetime,
) -> None:
    """Create one planning task for current user."""
    response = client.post(
        "/planning/tasks",
        headers=headers,
        json={
            "title": title,
            "description": description,
            "priority": "medium",
            "status": "pending",
            "estimated_minutes": 45,
            "deadline_at": None,
            "planned_start_at": planned_start_at.isoformat(),
            "planned_end_at": planned_end_at.isoformat(),
            "skill_id": None,
        },
    )
    assert response.status_code == 201


def _generate_scheduling_suggestion(
    client: httpx.Client,
    *,
    owner_headers: dict[str, str],
    team_id: int,
    participant_user_ids: list[int],
    collaboration_title: str,
    window_start_at: datetime,
    window_end_at: datetime,
) -> dict:
    """Generate one scheduling suggestion and return response payload."""
    response = client.post(
        "/scheduling/suggestions/generate",
        headers=owner_headers,
        json={
            "team_id": team_id,
            "participant_user_ids": participant_user_ids,
            "collaboration_title": collaboration_title,
            "skill_id": None,
            "window_start_at": window_start_at.isoformat(),
            "window_end_at": window_end_at.isoformat(),
            "minimum_duration_minutes": 30,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_mvp_scheduler_http_flow_end_to_end(api_client: httpx.Client) -> None:
    """Cover core HTTP flow from auth to applied suggestion and timetable read."""
    owner_auth, owner_id, owner_headers = _register_auth_user(
        api_client,
        email="owner-http@example.com",
        username="owner_http",
    )
    _, participant_id, participant_headers = _register_auth_user(
        api_client,
        email="participant-http@example.com",
        username="participant_http",
    )
    created_team_id = _create_team_workspace(
        api_client,
        owner_headers=owner_headers,
        name="HTTP Alpha Team",
        description="MVP http smoke team",
    )
    _add_team_participant(
        api_client,
        owner_headers=owner_headers,
        team_id=created_team_id,
        participant_user_id=participant_id,
    )

    current_time = datetime.now(UTC).replace(second=0, microsecond=0)
    _create_planning_task(
        api_client,
        headers=owner_headers,
        title="Owner focus task",
        description="Owner work",
        planned_start_at=current_time + timedelta(minutes=30),
        planned_end_at=current_time + timedelta(minutes=90),
    )
    _create_planning_task(
        api_client,
        headers=participant_headers,
        title="Participant focus task",
        description="Participant work",
        planned_start_at=current_time + timedelta(minutes=20),
        planned_end_at=current_time + timedelta(minutes=80),
    )
    generated_suggestion = _generate_scheduling_suggestion(
        api_client,
        owner_headers=owner_headers,
        team_id=created_team_id,
        participant_user_ids=[owner_id, participant_id],
        collaboration_title="MVP collaboration block",
        window_start_at=current_time,
        window_end_at=current_time + timedelta(hours=4),
    )
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
    _, _, owner_headers = _register_auth_user(
        api_client,
        email="team-owner-http@example.com",
        username="team_owner_http",
    )
    _, member_user_id, _ = _register_auth_user(
        api_client,
        email="team-member-http@example.com",
        username="team_member_http",
    )
    _, _, outsider_headers = _register_auth_user(
        api_client,
        email="team-outsider-http@example.com",
        username="team_outsider_http",
    )
    created_team_id = _create_team_workspace(
        api_client,
        owner_headers=owner_headers,
        name="Restricted Team HTTP",
        description="Only members can read timetable",
    )
    _add_team_participant(
        api_client,
        owner_headers=owner_headers,
        team_id=created_team_id,
        participant_user_id=member_user_id,
    )

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
    _, owner_id, owner_headers = _register_auth_user(
        api_client,
        email="status-owner-http@example.com",
        username="status_owner_http",
    )
    _, participant_id, _ = _register_auth_user(
        api_client,
        email="status-participant-http@example.com",
        username="status_participant_http",
    )
    created_team_id = _create_team_workspace(
        api_client,
        owner_headers=owner_headers,
        name="Status Team HTTP",
        description="Apply state validation team",
    )
    _add_team_participant(
        api_client,
        owner_headers=owner_headers,
        team_id=created_team_id,
        participant_user_id=participant_id,
    )

    current_time = datetime.now(UTC).replace(second=0, microsecond=0)
    generated_suggestion = _generate_scheduling_suggestion(
        api_client,
        owner_headers=owner_headers,
        team_id=created_team_id,
        participant_user_ids=[owner_id, participant_id],
        collaboration_title="Reject then apply",
        window_start_at=current_time,
        window_end_at=current_time + timedelta(hours=2),
    )
    generated_suggestion_id = generated_suggestion["id"]

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
