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


OFFICIAL_PILLARS = [
    ("CONDICOES", "Condições e Organização do Trabalho", 1, 2),
    ("JORNADA", "Jornada de Trabalho", 2, 1),
    ("LIDERANCA", "Liderança e Comunicação", 3, 5),
    ("AMBIENTE", "Ambiente, Respeito e Segurança", 4, 5),
    ("ETICA", "Ética e Compliance", 5, 4),
    ("DESENVOLVIMENTO", "Reconhecimento e Desenvolvimento", 6, 2),
    ("REMUNERACAO", "Remuneração e Benefícios", 7, 2),
    ("SAUDE", "Saúde, Bem-estar e Equilíbrio", 8, 3),
    ("CONDICOES_AMBIENTE", "Ambiente e Condições de Trabalho", 9, 4),
    ("PERMANENCIA", "Permanência e Vínculo com a Empresa", 10, 2),
]


def configure_pillars_request(
    monkeypatch,
    *,
    roles=("ADMIN",),
    user=None,
    survey=None,
    definitions=None,
    answer_score_counts=(),
    respondent_counts=(),
):
    session = configure_management_request(
        monkeypatch, roles=roles, user=user, survey=survey or set_survey()
    )
    monkeypatch.setattr(
        management_repository,
        "get_pillar_definitions",
        lambda db, survey_id: list(OFFICIAL_PILLARS if definitions is None else definitions),
    )
    monkeypatch.setattr(
        management_repository,
        "get_pillar_answer_score_counts",
        lambda db, survey_id: list(answer_score_counts),
    )
    monkeypatch.setattr(
        management_repository,
        "get_pillar_respondent_counts",
        lambda db, survey_id: list(respondent_counts),
    )
    return session


@pytest.mark.parametrize("role", ["ADMIN", "MANAGEMENT", "SURVEY_ADMIN"])
def test_management_roles_can_access_pillars(monkeypatch, role):
    configure_pillars_request(monkeypatch, roles=(role,))

    response = client.get("/api/management/surveys/CLIMATE_2026/pillars")

    assert response.status_code == 200
    assert len(response.json()["pillars"]) == 10


@pytest.mark.parametrize(
    "access_type,roles",
    [("INTERNAL", ("COLLABORATOR",)), ("EXTERNAL", ("COLLABORATOR",))],
)
def test_collaborator_only_cannot_access_pillars(monkeypatch, access_type, roles):
    configure_pillars_request(
        monkeypatch,
        roles=roles,
        user=SimpleNamespace(id=17, status="ACTIVE", access_type=access_type),
    )

    response = client.get("/api/management/surveys/CLIMATE_2026/pillars")

    assert response.status_code == 403
    assert response.json() == {"detail": "MANAGEMENT_ACCESS_REQUIRED"}


def test_pillars_require_authenticated_session():
    app.dependency_overrides[get_db_session] = FakeSession

    response = client.get("/api/management/surveys/CLIMATE_2026/pillars")

    assert response.status_code == 401


def test_unknown_survey_returns_404_for_pillars(monkeypatch):
    configure_pillars_request(monkeypatch, survey=None)
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda db, code: None)

    response = client.get("/api/management/surveys/UNKNOWN/pillars")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


@pytest.mark.parametrize("status", ["DRAFT", "ACTIVE", "CLOSED"])
def test_pillars_can_be_read_for_any_survey_status(monkeypatch, status):
    configure_pillars_request(monkeypatch, survey=set_survey(status=status))

    response = client.get("/api/management/surveys/CLIMATE_2026/pillars")

    assert response.status_code == 200
    assert response.json()["survey_status"] == status


def test_returns_ten_official_pillars_in_questionnaire_order(monkeypatch):
    configure_pillars_request(monkeypatch)

    payload = client.get("/api/management/surveys/CLIMATE_2026/pillars").json()

    assert [(pillar["code"], pillar["title"]) for pillar in payload["pillars"]] == [
        (code, title) for code, title, _, _ in OFFICIAL_PILLARS
    ]
    assert [pillar["question_count"] for pillar in payload["pillars"]] == [
        count for _, _, _, count in OFFICIAL_PILLARS
    ]


def test_pillars_http_payload_contains_no_internal_identifiers(monkeypatch):
    configure_pillars_request(monkeypatch)

    payload = client.get("/api/management/surveys/CLIMATE_2026/pillars").json()
    forbidden = {
        "question_id", "section_id", "option_id", "answer_id", "response_id", "user_id", "email"
    }

    assert forbidden.isdisjoint(payload)
    assert all(forbidden.isdisjoint(pillar) for pillar in payload["pillars"])


def test_pillar_answer_query_uses_only_score_likert_and_anonymous_tables():
    session = FakeSession(rows=[])

    management_repository.get_pillar_answer_score_counts(session, survey_id=301)

    statement = session.statements[0].compile()
    sql = str(statement).lower()
    params = list(statement.params.values())
    assert "response_answers" in sql
    assert "response_answer_options" in sql
    assert "survey_question_options" in sql
    assert "survey_questions" in sql
    assert "users" not in sql
    assert "user_roles" not in sql
    assert "survey_participation" not in sql
    assert {"SCORE", "LIKERT"}.issubset(params)


def test_pillar_definition_query_excludes_categories_by_database_definition():
    session = FakeSession(rows=[])

    management_repository.get_pillar_definitions(session, survey_id=301)

    statement = session.statements[0].compile()
    sql = str(statement).lower()
    params = list(statement.params.values())
    assert "survey_sections" in sql
    assert "survey_questions" in sql
    assert "LIKERT" in params
    assert any(value == ["SCORE", "MIXED"] for value in params)
    assert "order by survey_sections.position" in sql
    assert "survey_participation" not in sql
    assert "users" not in sql


def test_pillar_respondent_query_counts_distinct_anonymous_responses_with_valid_scores():
    session = FakeSession(rows=[("LIDERANCA", 5)])

    result = management_repository.get_pillar_respondent_counts(session, survey_id=301)

    statement = session.statements[0].compile()
    sql = str(statement).lower()
    params = list(statement.params.values())
    assert result == [("LIDERANCA", 5)]
    assert "count(distinct response_answers.response_id)" in sql
    assert {"SCORE", "LIKERT", 1, 5}.issubset(params)
    assert "survey_participation" not in sql
    assert "users" not in sql


@pytest.mark.parametrize(
    "score,expected",
    [(1, 0), (2, 25), (3, 50), (4, 75), (5, 100)],
)
def test_likert_scores_map_to_zero_to_one_hundred(score, expected):
    assert management_service._calculate_pillar_index([(score, 1)]) == expected


def test_pillar_formula_average_is_75_for_official_example():
    assert management_service._calculate_pillar_index([(4, 2), (5, 1), (3, 1)]) == 75.0


def test_pillar_index_rounds_to_two_decimal_places():
    assert management_service._calculate_pillar_index([(1, 1), (2, 2)]) == 16.67


def test_invalid_pillar_scores_are_ignored_without_breaking_analytics(monkeypatch, caplog):
    survey = set_survey(min_group_size=5)
    configure_pillars_request(
        monkeypatch,
        survey=survey,
        answer_score_counts=[("CONDICOES", 9, 2), ("CONDICOES", None, 1), ("CONDICOES", 4, 5)],
        respondent_counts=[("CONDICOES", 5)],
    )

    result = management_service.get_survey_pillars(FakeSession(), "CLIMATE_2026")
    first_pillar = result["pillars"][0]

    assert first_pillar["analytics_available"] is True
    assert first_pillar["index"] == 75.0
    assert "management pillar invalid option scores ignored" in caplog.text
    assert "response_id" not in caplog.text


def test_pillar_without_valid_responses_is_suppressed(monkeypatch):
    configure_pillars_request(monkeypatch)

    result = management_service.get_survey_pillars(FakeSession(), "CLIMATE_2026")
    first_pillar = result["pillars"][0]

    assert first_pillar["respondent_count"] == 0
    assert first_pillar["analytics_available"] is False
    assert first_pillar["index"] is None


def test_pillar_below_minimum_suppresses_index(monkeypatch):
    configure_pillars_request(
        monkeypatch,
        survey=set_survey(min_group_size=5),
        answer_score_counts=[("CONDICOES", 4, 8)],
        respondent_counts=[("CONDICOES", 4)],
    )

    result = management_service.get_survey_pillars(FakeSession(), "CLIMATE_2026")
    first_pillar = result["pillars"][0]

    assert first_pillar["respondent_count"] == 4
    assert first_pillar["analytics_available"] is False
    assert first_pillar["index"] is None


@pytest.mark.parametrize("respondent_count", [5, 8])
def test_pillar_at_or_above_minimum_releases_index(monkeypatch, respondent_count):
    configure_pillars_request(
        monkeypatch,
        survey=set_survey(min_group_size=5),
        answer_score_counts=[("CONDICOES", 4, respondent_count)],
        respondent_counts=[("CONDICOES", respondent_count)],
    )

    result = management_service.get_survey_pillars(FakeSession(), "CLIMATE_2026")
    first_pillar = result["pillars"][0]

    assert first_pillar["analytics_available"] is True
    assert first_pillar["index"] == 75.0


def test_each_pillar_uses_minimum_group_size_from_survey(monkeypatch):
    configure_pillars_request(
        monkeypatch,
        survey=set_survey(min_group_size=7),
        respondent_counts=[("CONDICOES", 6), ("JORNADA", 7)],
        answer_score_counts=[("CONDICOES", 4, 10), ("JORNADA", 4, 10)],
    )

    result = management_service.get_survey_pillars(FakeSession(), "CLIMATE_2026")

    assert result["min_group_size"] == 7
    assert result["pillars"][0]["analytics_available"] is False
    assert result["pillars"][0]["index"] is None
    assert result["pillars"][1]["analytics_available"] is True
    assert result["pillars"][1]["index"] == 75.0
