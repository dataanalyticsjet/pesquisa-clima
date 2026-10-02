from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user, get_db_session
from app.core import auth as auth_core
from app.main import app
from app.repositories import management_repository
from app.services import management_service
from app.services.organization_catalog import (
    REGIONAL_SC_CATALOG,
    OrganizationCatalogService,
    organization_catalog_service,
)


client = TestClient(app)


class FakeSession:
    def __init__(self):
        self.statements = []

    def scalar(self, statement):
        self.statements.append(statement)
        return None

    def execute(self, statement):
        self.statements.append(statement)
        return SimpleNamespace(all=lambda: [])


@pytest.fixture(autouse=True)
def clean_dependencies():
    client.cookies.clear()
    app.dependency_overrides.clear()
    yield
    client.cookies.clear()
    app.dependency_overrides.clear()


def survey(*, status="DRAFT", minimum=5, survey_id=701):
    return SimpleNamespace(
        id=survey_id,
        code="CLIMATE_2026",
        status=status,
        min_group_size=minimum,
    )


QUESTION_DEFINITIONS = [
    (44, "Q4", "Pergunta elegível 4", 4),
    (45, "Q5", "Pergunta elegível 5", 5),
]


def configure_service(monkeypatch, *, current_survey=None, group_counts=(), score_counts=(), question_counts=(), questions=None, catalog=None):
    monkeypatch.setattr(
        management_repository, "get_survey_by_code", lambda _db, _code: current_survey or survey()
    )
    monkeypatch.setattr(
        management_repository,
        "get_attention_question_definitions",
        lambda _db, _survey_id: list(QUESTION_DEFINITIONS if questions is None else questions),
    )
    monkeypatch.setattr(
        management_repository,
        "get_attention_group_respondent_counts",
        lambda _db, _survey_id: list(group_counts),
    )
    monkeypatch.setattr(
        management_repository,
        "get_attention_score_counts",
        lambda _db, _survey_id: list(score_counts),
    )
    monkeypatch.setattr(
        management_repository,
        "get_attention_question_respondent_counts",
        lambda _db, _survey_id: list(question_counts),
    )
    if catalog is not None:
        monkeypatch.setattr(organization_catalog_service, "get_regional_sc_catalog", lambda: tuple(catalog))
    return management_service.get_survey_attention(FakeSession(), "CLIMATE_2026")


def find_regional(payload, code):
    return next(item for item in payload["regionals"] if item["regional_code"] == code)


def find_sc(regional, code):
    return next(item for item in regional["scs"] if item["sc_code"] == code)


def test_catalog_contains_all_eight_regionals_and_26_service_centers():
    assert [entry.code for entry in REGIONAL_SC_CATALOG] == [
        "BA", "CE", "GP", "MG/SPN", "PR", "RJ", "SPE", "SPS"
    ]
    assert sum(len(entry.service_centers) for entry in REGIONAL_SC_CATALOG) == 26


@pytest.mark.parametrize(
    "regional,expected",
    [
        ("BA", ["AJU", "FEC", "VDC"]),
        ("CE", ["FOR", "JGS", "THE"]),
        ("GP", ["ANA", "BSB", "CGB", "CGR", "GYN", "MRB", "PMW", "PVH", "STM"]),
        ("MG/SPN", ["CGE", "CVH", "RAO", "RBP"]),
        ("PR", ["BNU", "NSR", "SJS"]),
        ("RJ", ["SJM", "SRR-ES"]),
        ("SPE", ["GRU"]),
        ("SPS", ["BRE"]),
    ],
)
def test_catalog_has_official_sc_codes_in_source_order(regional, expected):
    entry = next(item for item in REGIONAL_SC_CATALOG if item.code == regional)
    assert [sc.code for sc in entry.service_centers] == expected


def test_catalog_formats_display_name_and_does_not_invent_cnpj():
    aju = REGIONAL_SC_CATALOG[0].service_centers[0]
    assert aju.display_name == "AJU — SE - ARACAJU"
    assert all("cnpj" not in sc.__dict__ for regional in REGIONAL_SC_CATALOG for sc in regional.service_centers)
    assert OrganizationCatalogService().validate_selection("ORG_CNPJ", "invented") is False


@pytest.mark.parametrize("score,expected_rate", [(1, 100.0), (2, 100.0), (3, 0.0), (4, 0.0), (5, 0.0)])
def test_attention_rate_classifies_official_likert_scores(score, expected_rate, monkeypatch):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", 5)],
        score_counts=[("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, score, 5)],
        question_counts=[("REGIONAL", "BA", 44, 5)],
    )

    assert find_regional(payload, "BA")["attention_rate"] == expected_rate


def test_attention_rate_is_negative_answers_over_all_valid_answers():
    assert management_service._attention_rate(3, 8) == 37.5
    assert management_service._attention_rate(0, 4) == 0
    assert management_service._attention_rate(1, 0) is None


def test_group_rate_uses_weighted_answers_not_mean_of_question_percentages(monkeypatch):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", 5)],
        score_counts=[
            ("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, 1, 1),
            ("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, 5, 4),
            ("REGIONAL", "BA", 45, "Q5", "Pergunta elegível 5", 5, 2, 1),
            ("REGIONAL", "BA", 45, "Q5", "Pergunta elegível 5", 5, 5, 1),
        ],
        question_counts=[("REGIONAL", "BA", 44, 5), ("REGIONAL", "BA", 45, 5)],
    )

    ba = find_regional(payload, "BA")
    assert ba["attention_rate"] == 28.57
    assert [q["question_code"] for q in ba["questions"]] == ["Q5", "Q4"]
    assert [q["attention_rate"] for q in ba["questions"]] == [50.0, 20.0]


def test_every_catalog_group_and_eligible_question_is_returned_with_zero_counts(monkeypatch):
    payload = configure_service(monkeypatch)

    assert len(payload["regionals"]) == 8
    assert sum(len(region["scs"]) for region in payload["regionals"]) == 26
    for regional in payload["regionals"]:
        assert regional["respondent_count"] == 0
        assert regional["analytics_available"] is False
        assert regional["attention_rate"] is None
        assert [q["question_code"] for q in regional["questions"]] == ["Q4", "Q5"]
        for sc in regional["scs"]:
            assert sc["respondent_count"] == 0
            assert sc["analytics_available"] is False
            assert sc["attention_rate"] is None
            assert [q["question_code"] for q in sc["questions"]] == ["Q4", "Q5"]


def test_zero_through_below_minimum_group_counts_are_not_exposed(monkeypatch):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", 0), ("REGIONAL", "CE", 4)],
        score_counts=[("REGIONAL", "CE", 44, "Q4", "Pergunta elegível 4", 4, 1, 4)],
        question_counts=[("REGIONAL", "CE", 44, 4)],
    )
    ba = find_regional(payload, "BA")
    ce = find_regional(payload, "CE")

    assert ba["respondent_count"] == 0
    assert ba["attention_rate"] is None
    assert ce["respondent_count"] is None
    assert ce["analytics_available"] is False
    assert ce["attention_rate"] is None
    assert ce["questions"][0]["respondent_count"] is None
    assert ce["questions"][0]["attention_rate"] is None


@pytest.mark.parametrize("count", [5, 8])
def test_minimum_or_more_releases_rates_and_exact_counts(monkeypatch, count):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", count)],
        score_counts=[("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, 2, count)],
        question_counts=[("REGIONAL", "BA", 44, count)],
    )
    ba = find_regional(payload, "BA")

    assert ba["respondent_count"] == count
    assert ba["analytics_available"] is True
    assert ba["attention_rate"] == 100.0
    assert ba["questions"][0]["respondent_count"] == count
    assert ba["questions"][0]["attention_rate"] == 100.0


def test_invalid_scores_are_ignored_and_logged_generically(monkeypatch, caplog):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", 5)],
        score_counts=[
            ("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, None, 2),
            ("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, 9, 3),
            ("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, 2, 5),
        ],
        question_counts=[("REGIONAL", "BA", 44, 5)],
    )
    ba = find_regional(payload, "BA")

    assert ba["attention_rate"] == 100.0
    assert "management attention invalid score ignored" in caplog.text
    assert "response_id" not in caplog.text
    assert "user_id" not in caplog.text


def test_catalog_order_is_stable_for_equal_regional_and_sc_rates(monkeypatch):
    group_counts = [("REGIONAL", code, 5) for code in ("BA", "CE")]
    question_counts = []
    score_counts = []
    for regional in ("BA", "CE"):
        question_counts.append(("REGIONAL", regional, 44, 5))
        score_counts.append(("REGIONAL", regional, 44, "Q4", "Pergunta elegível 4", 4, 1, 1))
    group_counts.extend([("BASE", "AJU", 5), ("BASE", "FEC", 5)])
    for sc in ("AJU", "FEC"):
        question_counts.append(("BASE", sc, 44, 5))
        score_counts.append(("BASE", sc, 44, "Q4", "Pergunta elegível 4", 4, 1, 1))

    payload = configure_service(
        monkeypatch,
        group_counts=group_counts,
        question_counts=question_counts,
        score_counts=score_counts,
    )
    available_regions = [region["regional_code"] for region in payload["regionals"] if region["analytics_available"]]
    ba = find_regional(payload, "BA")

    assert available_regions == ["BA", "CE"]
    assert [sc["sc_code"] for sc in ba["scs"] if sc["analytics_available"]] == ["AJU", "FEC"]


def test_groups_with_data_are_sorted_by_attention_rate_and_no_group_is_dropped(monkeypatch):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", 5), ("REGIONAL", "CE", 5), ("REGIONAL", "GP", 2)],
        score_counts=[
            ("REGIONAL", "BA", 44, "Q4", "Pergunta elegível 4", 4, 5, 5),
            ("REGIONAL", "CE", 44, "Q4", "Pergunta elegível 4", 4, 1, 4),
            ("REGIONAL", "CE", 44, "Q4", "Pergunta elegível 4", 4, 5, 1),
            ("REGIONAL", "GP", 44, "Q4", "Pergunta elegível 4", 4, 1, 2),
        ],
        question_counts=[("REGIONAL", "BA", 44, 5), ("REGIONAL", "CE", 44, 5), ("REGIONAL", "GP", 44, 2)],
    )

    assert [item["regional_code"] for item in payload["regionals"][:2]] == ["CE", "BA"]
    assert payload["regionals"][2]["regional_code"] == "GP"
    assert len(payload["regionals"]) == 8
    assert sum(len(item["scs"]) for item in payload["regionals"]) == 26


def test_question_suppressed_by_minimum_remains_in_the_response(monkeypatch):
    payload = configure_service(
        monkeypatch,
        group_counts=[("REGIONAL", "BA", 5)],
        score_counts=[("REGIONAL", "BA", 45, "Q5", "Pergunta elegível 5", 5, 1, 5)],
        question_counts=[("REGIONAL", "BA", 45, 5), ("REGIONAL", "BA", 44, 2)],
    )
    questions = find_regional(payload, "BA")["questions"]

    assert [question["question_code"] for question in questions] == ["Q5", "Q4"]
    assert questions[0]["analytics_available"] is True
    assert questions[1]["analytics_available"] is False
    assert questions[1]["respondent_count"] is None
    assert questions[1]["attention_rate"] is None


def test_payload_contains_no_internal_or_respondent_identifiers(monkeypatch):
    payload = configure_service(monkeypatch)
    serialized = str(payload).lower()
    forbidden = ("response_id", "user_id", "email", "answer_id", "question_id", "survey_id", "open_id", "union_id")

    assert all(key not in serialized for key in forbidden)
    assert "regional_id" not in serialized
    assert "cnpj" not in serialized


def test_repository_queries_use_only_survey_definition_and_anonymous_tables():
    session = FakeSession()
    management_repository.get_attention_question_definitions(session, 701)
    management_repository.get_attention_group_respondent_counts(session, 701)
    management_repository.get_attention_score_counts(session, 701)
    management_repository.get_attention_question_respondent_counts(session, 701)

    sql = [str(statement.compile()).lower() for statement in session.statements]
    assert "analysis_role" in sql[0] and "question_type" in sql[0]
    for statement in sql[1:]:
        assert "anonymous_response_segments" in statement
        assert "users" not in statement
        assert "survey_participation" not in statement
        assert "user_roles" not in statement
    assert "response_id" not in sql[0]
    assert "distinct response_answers.response_id" in sql[1]
    assert "anonymous_responses" in sql[1]
    assert "score_value between" in sql[1]
    assert "distinct response_answers.id" in sql[2]
    assert "distinct response_answers.response_id" in sql[3]
    assert all("join users" not in statement for statement in sql)


def test_repository_filters_question_scores_by_official_fields_and_bounds():
    session = FakeSession()
    management_repository.get_attention_question_definitions(session, 701)
    management_repository.get_attention_score_counts(session, 701)
    definition = session.statements[0].compile()
    definition_params = list(definition.params.values())
    definition_sql = str(definition).lower()
    assert {"SCORE", "LIKERT"}.issubset(definition_params)
    assert "survey_questions.code =" not in definition_sql

    statement = session.statements[1].compile()
    params = list(statement.params.values())
    sql = str(statement).lower()

    flattened_params = [item for value in params for item in (value if isinstance(value, list) else [value])]
    assert {"SCORE", "LIKERT", "REGIONAL", "BASE"}.issubset(flattened_params)
    assert "survey_question_options.score_value" in sql
    assert "survey_question_options.score_value between" not in sql


def configure_attention_request(monkeypatch, *, roles=("ADMIN",), current_survey=None, user=None):
    db = FakeSession()
    app.dependency_overrides[get_current_user] = lambda: user or SimpleNamespace(
        id=17, status="ACTIVE", access_type="INTERNAL"
    )
    app.dependency_overrides[get_db_session] = lambda: db
    monkeypatch.setattr(auth_core.identity_repository, "get_user_roles", lambda _db, _user_id: list(roles))
    monkeypatch.setattr(
        management_repository, "get_survey_by_code", lambda _db, _code: current_survey
    )
    monkeypatch.setattr(management_repository, "get_attention_question_definitions", lambda _db, _id: [])
    monkeypatch.setattr(management_repository, "get_attention_group_respondent_counts", lambda _db, _id: [])
    monkeypatch.setattr(management_repository, "get_attention_score_counts", lambda _db, _id: [])
    monkeypatch.setattr(management_repository, "get_attention_question_respondent_counts", lambda _db, _id: [])
    return db


@pytest.mark.parametrize("role", ["ADMIN", "MANAGEMENT", "SURVEY_ADMIN"])
def test_management_roles_can_access_attention(monkeypatch, role):
    configure_attention_request(monkeypatch, roles=(role,), current_survey=survey())

    response = client.get("/api/management/surveys/CLIMATE_2026/attention")

    assert response.status_code == 200
    assert len(response.json()["regionals"]) == 8


@pytest.mark.parametrize("access_type", ["INTERNAL", "EXTERNAL"])
def test_collaborator_only_is_forbidden_from_attention(monkeypatch, access_type):
    configure_attention_request(
        monkeypatch,
        roles=("COLLABORATOR",),
        current_survey=survey(),
        user=SimpleNamespace(id=17, status="ACTIVE", access_type=access_type),
    )

    response = client.get("/api/management/surveys/CLIMATE_2026/attention")

    assert response.status_code == 403
    assert response.json() == {"detail": "MANAGEMENT_ACCESS_REQUIRED"}


def test_attention_requires_session():
    app.dependency_overrides[get_db_session] = FakeSession

    response = client.get("/api/management/surveys/CLIMATE_2026/attention")

    assert response.status_code == 401


def test_unknown_survey_returns_404_for_attention(monkeypatch):
    configure_attention_request(monkeypatch)

    response = client.get("/api/management/surveys/UNKNOWN/attention")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


@pytest.mark.parametrize("status", ["DRAFT", "ACTIVE", "CLOSED"])
def test_attention_allows_every_survey_status(monkeypatch, status):
    configure_attention_request(monkeypatch, current_survey=survey(status=status))

    response = client.get("/api/management/surveys/CLIMATE_2026/attention")

    assert response.status_code == 200
    assert response.json()["survey_status"] == status


def test_attention_payload_omits_internal_ids_and_catalog_has_no_cnpj(monkeypatch):
    configure_attention_request(monkeypatch, current_survey=survey())

    response = client.get("/api/management/surveys/CLIMATE_2026/attention")
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) == {"survey_code", "survey_status", "min_group_size", "regionals"}
    assert all("regional_id" not in item for item in payload["regionals"])
    assert all("sc_id" not in sc for item in payload["regionals"] for sc in item["scs"])
    assert all("cnpj" not in sc for item in payload["regionals"] for sc in item["scs"])


def test_catalog_entry_is_shared_with_submission_validation():
    catalog = OrganizationCatalogService()
    assert catalog.get_regional_sc_catalog() is REGIONAL_SC_CATALOG
    assert catalog.validate_selection("ORG_REGIONAL", "BA") is True
    assert catalog.validate_selection("ORG_REGIONAL", "NOT-A-REGION") is False
    assert catalog.validate_selection("ORG_BASE", "AJU", regional_code="BA") is True
    assert catalog.validate_selection("ORG_BASE", "INVALID", regional_code="BA") is False
    assert catalog.validate_selection("ORG_BASE", "GRU", regional_code="BA") is False
    assert catalog.validate_selection("ORG_BASE", "GRU", regional_code="SPE") is True
    assert catalog.validate_selection("ORG_BASE", "BRE", regional_code="SPS") is True
