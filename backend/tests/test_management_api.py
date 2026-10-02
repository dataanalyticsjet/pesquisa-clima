from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core import auth as auth_core
from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.repositories import management_repository
from app.services import management_service


client = TestClient(app)


class FakeSession:
    def __init__(self, scalar_values=(), rows=()):
        self.scalar_values = list(scalar_values)
        self.rows = list(rows)
        self.statements = []

    def scalar(self, statement):
        self.statements.append(statement)
        return self.scalar_values.pop(0) if self.scalar_values else None

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


def configure_management_request(monkeypatch, *, roles=("ADMIN",), user=None, survey=None):
    user = user or SimpleNamespace(id=17, status="ACTIVE", access_type="INTERNAL")
    session = FakeSession()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: session
    monkeypatch.setattr(auth_core.identity_repository, "get_user_roles", lambda db, user_id: list(roles))
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda db, code: survey)
    monkeypatch.setattr(management_repository, "count_completed_participations", lambda db, survey_id: 0)
    monkeypatch.setattr(management_repository, "count_anonymous_responses", lambda db, survey_id: 0)
    monkeypatch.setattr(management_repository, "get_q39_score_counts", lambda db, survey_id: [])
    return session


def set_survey(*, status="DRAFT", min_group_size=5, survey_id=301):
    return SimpleNamespace(
        id=survey_id,
        code="CLIMATE_2026",
        status=status,
        min_group_size=min_group_size,
    )


@pytest.mark.parametrize("role", ["ADMIN", "MANAGEMENT", "SURVEY_ADMIN"])
def test_management_roles_can_access_overview(monkeypatch, role):
    configure_management_request(monkeypatch, roles=(role,), survey=set_survey())

    response = client.get("/api/management/surveys/CLIMATE_2026/overview")

    assert response.status_code == 200
    assert response.json()["survey_status"] == "DRAFT"
    assert response.json()["completed_participations"] == 0
    assert response.json()["anonymous_response_count"] == 0


@pytest.mark.parametrize(
    "access_type,roles",
    [("INTERNAL", ("COLLABORATOR",)), ("EXTERNAL", ("COLLABORATOR",))],
)
def test_collaborator_only_is_forbidden(monkeypatch, access_type, roles):
    configure_management_request(
        monkeypatch,
        roles=roles,
        user=SimpleNamespace(id=17, status="ACTIVE", access_type=access_type),
        survey=set_survey(),
    )

    response = client.get("/api/management/surveys/CLIMATE_2026/overview")

    assert response.status_code == 403
    assert response.json() == {"detail": "MANAGEMENT_ACCESS_REQUIRED"}


def test_management_overview_requires_session():
    app.dependency_overrides[get_db_session] = FakeSession

    response = client.get("/api/management/surveys/CLIMATE_2026/overview")

    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHENTICATED"}


def test_inactive_user_is_blocked_by_existing_auth_dependency(monkeypatch):
    request = SimpleNamespace(session={"user_id": 17})
    inactive = SimpleNamespace(id=17, status="INACTIVE")
    monkeypatch.setattr(auth_core, "get_user_by_id", lambda session, user_id: inactive)

    with pytest.raises(HTTPException) as error:
        get_current_user(request, FakeSession())

    assert error.value.status_code == 401
    assert request.session == {}


def test_unknown_survey_returns_404(monkeypatch):
    configure_management_request(monkeypatch, survey=None)

    response = client.get("/api/management/surveys/UNKNOWN/overview")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


@pytest.mark.parametrize("status", ["DRAFT", "ACTIVE", "CLOSED"])
def test_overview_can_read_surveys_in_any_lifecycle_status(monkeypatch, status):
    configure_management_request(monkeypatch, survey=set_survey(status=status))

    response = client.get("/api/management/surveys/CLIMATE_2026/overview")

    assert response.status_code == 200
    assert response.json()["survey_status"] == status


def test_zero_counts_are_returned_from_their_separate_sources(monkeypatch):
    session = FakeSession(scalar_values=[0, 0])

    completed = management_repository.count_completed_participations(session, survey_id=301)
    anonymous = management_repository.count_anonymous_responses(session, survey_id=301)

    assert completed == 0
    assert anonymous == 0
    assert len(session.statements) == 2
    participation_sql = str(session.statements[0]).lower()
    anonymous_sql = str(session.statements[1]).lower()
    assert "survey_participation" in participation_sql
    assert "anonymous_responses" not in participation_sql
    assert "anonymous_responses" in anonymous_sql
    assert "survey_participation" not in anonymous_sql
    assert " join " not in participation_sql
    assert " join " not in anonymous_sql


def test_nps_query_uses_only_anonymous_response_tables():
    session = FakeSession(rows=[(0, 1), (7, 1), (10, 3)])

    counts = management_repository.get_q39_score_counts(session, survey_id=301)

    statement = str(session.statements[0]).lower()
    assert counts == [(0, 1), (7, 1), (10, 3)]
    assert "response_answers" in statement
    assert "response_answer_options" in statement
    assert "survey_question_options" in statement
    assert "survey_questions" in statement
    assert "users" not in statement
    assert "user_roles" not in statement
    assert "survey_participation" not in statement


def test_service_uses_anonymous_response_count_for_privacy_and_keeps_counts_separate(monkeypatch):
    survey = set_survey(min_group_size=5)
    calls = []
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda db, code: survey)
    monkeypatch.setattr(management_repository, "count_completed_participations", lambda db, sid: calls.append(("participation", sid)) or 2)
    monkeypatch.setattr(management_repository, "count_anonymous_responses", lambda db, sid: calls.append(("anonymous", sid)) or 3)
    monkeypatch.setattr(management_repository, "get_q39_score_counts", lambda db, sid: pytest.fail("NPS must be suppressed"))

    result = management_service.get_survey_overview(FakeSession(), "CLIMATE_2026")

    assert calls == [("participation", 301), ("anonymous", 301)]
    assert result["completed_participations"] == 2
    assert result["anonymous_response_count"] == 3
    assert result["respondent_count"] == 3


def test_nps_is_suppressed_below_min_group_size(monkeypatch):
    survey = set_survey(min_group_size=5)
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda db, code: survey)
    monkeypatch.setattr(management_repository, "count_completed_participations", lambda db, sid: 4)
    monkeypatch.setattr(management_repository, "count_anonymous_responses", lambda db, sid: 4)
    monkeypatch.setattr(management_repository, "get_q39_score_counts", lambda db, sid: pytest.fail("NPS must be suppressed"))

    result = management_service.get_survey_overview(FakeSession(), "CLIMATE_2026")

    assert result["analytics_available"] is False
    assert result["nps"] is None
    assert result["respondent_count"] == 4


def test_exactly_min_group_size_allows_nps_calculation(monkeypatch):
    survey = set_survey(min_group_size=5)
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda db, code: survey)
    monkeypatch.setattr(management_repository, "count_completed_participations", lambda db, sid: 5)
    monkeypatch.setattr(management_repository, "count_anonymous_responses", lambda db, sid: 5)
    monkeypatch.setattr(management_repository, "get_q39_score_counts", lambda db, sid: [(0, 1), (7, 3), (10, 1)])

    result = management_service.get_survey_overview(FakeSession(), "CLIMATE_2026")

    assert result["analytics_available"] is True
    assert result["nps"] == 0


@pytest.mark.parametrize(
    "score_counts,expected",
    [([(0, 1)], -100), ([(7, 1)], 0), ([(10, 1)], 100)],
)
def test_nps_score_classifies_detractors_neutrals_and_promoters(score_counts, expected):
    nps, count = management_service._calculate_nps(score_counts)

    assert nps == expected
    assert count == 1


def test_nps_uses_promoter_minus_detractor_percentages_with_neutrals_in_denominator():
    nps, count = management_service._calculate_nps([(0, 2), (6, 1), (7, 2), (8, 1), (9, 3), (10, 1)])

    assert count == 10
    assert nps == 10


def test_no_q39_answers_returns_null_nps():
    assert management_service._calculate_nps([]) == (None, 0)


def test_response_contains_no_internal_or_identity_identifiers(monkeypatch):
    configure_management_request(monkeypatch, survey=set_survey())

    payload = client.get("/api/management/surveys/CLIMATE_2026/overview").json()

    forbidden = {
        "user_id", "email", "response_id", "answer_id", "participation_id",
        "survey_id", "open_id", "union_id",
    }
    assert forbidden.isdisjoint(payload)


def test_invited_and_adherence_metrics_remain_unavailable(monkeypatch):
    configure_management_request(monkeypatch, survey=set_survey())

    payload = client.get("/api/management/surveys/CLIMATE_2026/overview").json()

    assert payload["invited_count"] is None
    assert payload["adherence_percent"] is None
    assert payload["invited_population_source_configured"] is False
    assert not {5842, 4291, 73.45, 1551, 72, 38}.intersection(payload.values())


def test_http_response_matches_overview_schema_and_uses_survey_min_group_size(monkeypatch):
    survey = set_survey(min_group_size=7)
    configure_management_request(monkeypatch, survey=survey)

    payload = client.get("/api/management/surveys/CLIMATE_2026/overview").json()

    assert payload == {
        "survey_code": "CLIMATE_2026",
        "survey_status": "DRAFT",
        "min_group_size": 7,
        "completed_participations": 0,
        "anonymous_response_count": 0,
        "respondent_count": 0,
        "analytics_available": False,
        "nps": None,
        "invited_count": None,
        "adherence_percent": None,
        "invited_population_source_configured": False,
    }


def test_repository_nps_query_finds_official_question_by_q39_code():
    session = FakeSession(rows=[])

    management_repository.get_q39_score_counts(session, survey_id=301)

    compiled = session.statements[0].compile()
    statement = str(compiled)
    assert "survey_questions.code = :code_1" in statement
    assert "Q39" in compiled.params.values()
