from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import database as database_api
from app.core import auth as auth_core
from app.main import app
from app.repositories import identity_repository
from app.services.database_health import DatabaseNotConfiguredError


client = TestClient(app)


@pytest.fixture
def admin_access(monkeypatch):
    client.app.dependency_overrides.clear()
    client.app.dependency_overrides[auth_core.get_current_user] = lambda: SimpleNamespace(id=12)
    client.app.dependency_overrides[auth_core.get_db_session] = lambda: object()
    monkeypatch.setattr(identity_repository, "get_user_roles", lambda _session, _user_id: ["ADMIN"])
    yield
    client.app.dependency_overrides.clear()


def test_database_health_returns_expected_mocked_survey(monkeypatch, admin_access):
    expected = {
        "status": "ok",
        "database": "pesquisa_clima",
        "survey": {
            "code": "CLIMATE_2026",
            "status": "DRAFT",
            "version": 1,
            "min_group_size": 5,
        },
    }
    monkeypatch.setattr(database_api, "read_database_health", lambda: expected)

    response = client.get("/api/database/health")

    assert response.status_code == 200
    assert response.json() == expected


def test_database_health_failure_is_controlled(monkeypatch, admin_access):
    def fail():
        raise DatabaseNotConfiguredError("missing settings")

    monkeypatch.setattr(database_api, "read_database_health", fail)

    response = client.get("/api/database/health")

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Database health check failed.",
        }
    }


def test_database_health_never_exposes_connection_credentials(monkeypatch, admin_access):
    secret_values = ["db.internal.local", "private-user", "secret-password", "mysql+pymysql://"]

    def fail():
        raise RuntimeError(" ".join(secret_values))

    monkeypatch.setattr(database_api, "read_database_health", fail)

    response = client.get("/api/database/health")
    response_text = response.text

    assert response.status_code == 503
    for secret in secret_values:
        assert secret not in response_text


def test_database_health_requires_authentication():
    client.app.dependency_overrides.clear()
    client.app.dependency_overrides[auth_core.get_db_session] = lambda: object()

    response = client.get("/api/database/health")

    assert response.status_code == 401
    client.app.dependency_overrides.clear()


@pytest.mark.parametrize("role", ["COLLABORATOR", "MANAGEMENT", "SURVEY_ADMIN"])
def test_database_health_is_admin_only(monkeypatch, role):
    client.app.dependency_overrides.clear()
    client.app.dependency_overrides[auth_core.get_current_user] = lambda: SimpleNamespace(id=12)
    client.app.dependency_overrides[auth_core.get_db_session] = lambda: object()
    monkeypatch.setattr(identity_repository, "get_user_roles", lambda _session, _user_id: [role])

    response = client.get("/api/database/health")

    assert response.status_code == 403
    assert response.json() == {"detail": "ADMIN_ACCESS_REQUIRED"}
    client.app.dependency_overrides.clear()
