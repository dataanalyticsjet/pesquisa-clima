import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.security_middleware import MAX_REQUEST_BODY_BYTES
from app.main import app


client = TestClient(app, follow_redirects=False)


def test_debug_defaults_off_and_is_rejected_when_enabled_in_production():
    assert Settings(_env_file=None).app_debug is False
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", app_debug=True)


def test_api_responses_have_safe_headers_and_are_not_cached():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["cache-control"] == "no-store"


def test_unsafe_method_rejects_foreign_origin():
    response = client.post(
        "/api/auth/logout",
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "ORIGIN_NOT_ALLOWED"}


def test_unsafe_method_rejects_foreign_referer_when_origin_is_absent():
    response = client.post(
        "/api/auth/logout",
        headers={"Referer": "https://attacker.example/form"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "ORIGIN_NOT_ALLOWED"}


def test_production_unsafe_methods_use_configured_frontend_origin(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "frontend_base_url", "https://clima.example/login")
    allowed = client.post(
        "/api/auth/logout",
        headers={"Origin": "https://clima.example"},
    )
    rejected = client.post(
        "/api/auth/logout",
        headers={"Origin": "https://attacker.example"},
    )
    assert allowed.status_code == 200
    assert rejected.status_code == 403


def test_api_does_not_enable_cross_origin_cors():
    response = client.options(
        "/api/auth/logout",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 405
    assert "access-control-allow-origin" not in response.headers


def test_local_frontend_origin_is_allowed_for_development():
    response = client.post(
        "/api/auth/logout",
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_foreign_origin_cannot_be_overridden_by_allowed_referer():
    response = client.post(
        "/api/auth/logout",
        headers={
            "Origin": "https://attacker.example",
            "Referer": "http://127.0.0.1:3000/login",
        },
    )
    assert response.status_code == 403


def test_oversized_request_body_is_rejected_before_endpoint_validation():
    response = client.post(
        "/api/auth/external/request-code",
        content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "REQUEST_BODY_TOO_LARGE"}


def test_request_validation_does_not_echo_malformed_otp():
    submitted_code = "12345"
    response = client.post(
        "/api/auth/external/verify-code",
        json={"email": "person@example.com", "code": submitted_code},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "INVALID_REQUEST"}
    assert submitted_code not in response.text


def test_survey_code_path_length_is_bounded():
    response = client.get(f"/api/surveys/{'A' * 65}")
    assert response.status_code == 422
