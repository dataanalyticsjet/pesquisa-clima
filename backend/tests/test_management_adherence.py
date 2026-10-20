from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core import auth as auth_core
from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.repositories import management_repository
from app.services.organization_catalog import REGIONAL_SC_CATALOG


client = TestClient(app)


class FakeSession:
    def __init__(self, *, total=0, rows=()):
        self.total = total
        self.rows = list(rows)
        self.statements = []

    def scalar(self, statement):
        self.statements.append(statement)
        return self.total

    def execute(self, statement):
        self.statements.append(statement)
        return SimpleNamespace(all=lambda: self.rows)


@pytest.fixture(autouse=True)
def clean_dependencies():
    client.cookies.clear()
    app.dependency_overrides.clear()
    yield
    client.cookies.clear()
    app.dependency_overrides.clear()


def configure_request(monkeypatch, *, roles=("ADMIN",), total=0, regional_rows=(), survey_exists=True):
    user = SimpleNamespace(id=17, status="ACTIVE", access_type="INTERNAL")
    survey = SimpleNamespace(
        id=301,
        code="CLIMATE_2026",
        status="ACTIVE",
        min_group_size=5,
    ) if survey_exists else None
    session = FakeSession(total=total, rows=regional_rows)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: session
    monkeypatch.setattr(auth_core.identity_repository, "get_user_roles", lambda db, user_id: list(roles))
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda db, code: survey)
    monkeypatch.setattr(management_repository, "count_anonymous_responses", lambda db, survey_id: total)
    monkeypatch.setattr(
        management_repository,
        "get_anonymous_response_counts_by_regional",
        lambda db, survey_id: list(regional_rows),
    )
    return session


def test_regional_count_query_counts_distinct_anonymous_responses_only():
    session = FakeSession(total=0, rows=[("CE", 5), ("GP", 2)])

    result = management_repository.get_anonymous_response_counts_by_regional(session, survey_id=301)

    sql = str(session.statements[0].compile()).lower()
    params = list(session.statements[0].compile().params.values())
    assert result == [("CE", 5), ("GP", 2)]
    assert "anonymous_response_segments" in sql
    assert "anonymous_responses" in sql
    assert "count(distinct anonymous_response_segments.response_id)" in sql
    assert "survey_participation" not in sql
    assert "users" not in sql
    assert "response_answers" not in sql
    assert "response_answer_options" not in sql
    assert "REGIONAL" in params


def test_total_form_count_uses_distinct_anonymous_response_uuid():
    session = FakeSession(total=11)

    result = management_repository.count_anonymous_responses(session, survey_id=301)

    sql = str(session.statements[0].compile()).lower()
    assert result == 11
    assert "count(distinct anonymous_responses.response_id)" in sql
    assert "survey_participation" not in sql
    assert "users" not in sql


@pytest.mark.parametrize("role", ["ADMIN", "MANAGEMENT", "SURVEY_ADMIN"])
def test_management_roles_can_read_adherence(monkeypatch, role):
    configure_request(monkeypatch, roles=(role,), total=0)

    response = client.get("/api/management/surveys/CLIMATE_2026/adherence")

    assert response.status_code == 200
    assert response.json()["total_regionals"] == 10


@pytest.mark.parametrize("access_type", ["INTERNAL", "EXTERNAL"])
def test_collaborator_only_cannot_read_adherence(monkeypatch, access_type):
    user = SimpleNamespace(id=17, status="ACTIVE", access_type=access_type)
    configure_request(monkeypatch, roles=("COLLABORATOR",))
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/management/surveys/CLIMATE_2026/adherence")

    assert response.status_code == 403
    assert response.json() == {"detail": "MANAGEMENT_ACCESS_REQUIRED"}


def test_adherence_requires_session():
    app.dependency_overrides[get_db_session] = FakeSession

    response = client.get("/api/management/surveys/CLIMATE_2026/adherence")

    assert response.status_code == 401


def test_unknown_survey_returns_404(monkeypatch):
    configure_request(monkeypatch, survey_exists=False)

    response = client.get("/api/management/surveys/UNKNOWN/adherence")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


def test_adherence_returns_all_official_regionals_sorted_by_visible_counts(monkeypatch):
    configure_request(monkeypatch, total=13, regional_rows=[("GP", 8), ("CE", 5)])

    payload = client.get("/api/management/surveys/CLIMATE_2026/adherence").json()

    assert payload["total_responses"] == 13
    assert payload["total_regionals"] == 10
    assert payload["regionals_with_results"] == 2
    assert len(payload["regionals"]) == 10
    assert [item["regional_code"] for item in payload["regionals"][:2]] == ["GP", "CE"]
    assert {item["regional_code"] for item in payload["regionals"]} == {
        entry.code for entry in REGIONAL_SC_CATALOG
    }
    assert all(
        item["response_count"] == 0
        for item in payload["regionals"]
        if item["regional_code"] not in {"GP", "CE"}
    )
    forbidden = {"user_id", "email", "response_id", "participation_id", "answer_id"}
    assert forbidden.isdisjoint(payload)
    assert all(forbidden.isdisjoint(item) for item in payload["regionals"])
    assert "adherence_percent" not in payload


def test_small_regional_count_and_global_total_are_suppressed(monkeypatch):
    configure_request(monkeypatch, total=7, regional_rows=[("GP", 5), ("CE", 2)])

    payload = client.get("/api/management/surveys/CLIMATE_2026/adherence").json()
    by_code = {item["regional_code"]: item for item in payload["regionals"]}

    assert payload["total_responses"] is None
    assert payload["regionals_with_results"] == 1
    assert by_code["GP"]["response_count"] == 5
    assert by_code["CE"]["response_count"] is None
    assert by_code["CE"]["analytics_available"] is False


@pytest.mark.parametrize(
    "total,rows",
    [
        (6, [("GP", 5)]),  # one form has no Regional segment
        (8, [("GP", 5), ("UNLISTED", 3)]),  # non-catalog segment
    ],
)
def test_total_suppressed_when_regional_coverage_is_incomplete(monkeypatch, total, rows):
    configure_request(monkeypatch, total=total, regional_rows=rows)

    payload = client.get("/api/management/surveys/CLIMATE_2026/adherence").json()

    assert payload["total_responses"] is None
    assert len(payload["regionals"]) == 10


def test_zero_forms_returns_zero_for_every_official_regional(monkeypatch):
    configure_request(monkeypatch, total=0)

    payload = client.get("/api/management/surveys/CLIMATE_2026/adherence").json()

    assert payload["total_responses"] == 0
    assert payload["regionals_with_results"] == 0
    assert len(payload["regionals"]) == 10
    assert all(item["response_count"] == 0 for item in payload["regionals"])
