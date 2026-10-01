from fastapi.testclient import TestClient

from app.api import database as database_api
from app.main import app
from app.services.database_health import DatabaseNotConfiguredError


client = TestClient(app)


def test_database_health_returns_expected_mocked_survey(monkeypatch):
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


def test_database_health_failure_is_controlled(monkeypatch):
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


def test_database_health_never_exposes_connection_credentials(monkeypatch):
    secret_values = ["db.internal.local", "private-user", "secret-password", "mysql+pymysql://"]

    def fail():
        raise RuntimeError(" ".join(secret_values))

    monkeypatch.setattr(database_api, "read_database_health", fail)

    response = client.get("/api/database/health")
    response_text = response.text

    assert response.status_code == 503
    for secret in secret_values:
        assert secret not in response_text
