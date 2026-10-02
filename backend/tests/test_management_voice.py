from types import SimpleNamespace
import logging

import pytest
from fastapi.testclient import TestClient

from app.core import auth as auth_core
from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.repositories import management_repository
from app.services import management_service


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


def make_survey(*, status="DRAFT", minimum=5, survey_id=902):
    return SimpleNamespace(
        id=survey_id,
        code="CLIMATE_2026",
        status=status,
        min_group_size=minimum,
    )


QUESTION_DEFINITIONS = [
    ("Q40", "Que mudança ajudaria a organizar melhor a jornada de trabalho na sua área?", "TEXTAREA"),
    ("Q41", "O que a empresa poderia melhorar para tornar sua experiência de trabalho melhor?", "TEXTAREA"),
    ("Q42", "O que você mais valoriza em trabalhar na J&T Express?", "SHORT_TEXT"),
]


def configure_voice_service(
    monkeypatch,
    *,
    current_survey=None,
    definitions=None,
    respondent_counts=(),
    text_answers=(),
):
    monkeypatch.setattr(
        management_repository,
        "get_survey_by_code",
        lambda _db, _code: current_survey if current_survey is not None else make_survey(),
    )
    monkeypatch.setattr(
        management_repository,
        "get_voice_question_definitions",
        lambda _db, _survey_id: list(QUESTION_DEFINITIONS if definitions is None else definitions),
    )
    monkeypatch.setattr(
        management_repository,
        "get_voice_respondent_counts",
        lambda _db, _survey_id: list(respondent_counts),
    )
    monkeypatch.setattr(
        management_repository,
        "get_voice_text_answers",
        lambda _db, _survey_id: list(text_answers),
    )
    return management_service.get_survey_voice(FakeSession(), "CLIMATE_2026")


def question(payload, code):
    return next(item for item in payload["questions"] if item["question_code"] == code)


def test_service_uses_database_definition_text_and_types_for_q40_q41_q42(monkeypatch):
    payload = configure_voice_service(monkeypatch)

    assert [(item["question_code"], item["question_text"], item["question_type"]) for item in payload["questions"]] == QUESTION_DEFINITIONS
    assert [item["question_code"] for item in payload["questions"]] == ["Q40", "Q41", "Q42"]


def test_zero_responses_returns_zero_and_empty_content_for_each_question(monkeypatch):
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", 0), ("Q41", 0), ("Q42", 0)],
    )

    for code in ("Q40", "Q41"):
        item = question(payload, code)
        assert item["respondent_count"] == 0
        assert item["analytics_available"] is False
        assert item["comments"] == []
    q42 = question(payload, "Q42")
    assert q42["respondent_count"] == 0
    assert q42["analytics_available"] is False
    assert q42["terms"] == []


@pytest.mark.parametrize("code", ["Q40", "Q41", "Q42"])
def test_below_minimum_suppresses_counts_and_all_content(code, monkeypatch):
    rows = [(code, f"resposta privada {index}") for index in range(1, 4)]
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[(code, 3)],
        text_answers=rows,
    )
    item = question(payload, code)

    assert item["analytics_available"] is False
    assert item["respondent_count"] is None
    assert item.get("comments", []) == []
    assert item.get("terms", []) == []
    assert all("resposta privada" not in str(item) for item in payload["questions"] if item["question_code"] == code)


@pytest.mark.parametrize("count", [5, 8])
def test_exactly_minimum_and_above_release_text_and_count(count, monkeypatch):
    comments = [("Q40", f"Comentário original {index} ") for index in range(count)]
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", count)],
        text_answers=comments,
    )
    q40 = question(payload, "Q40")

    assert q40["analytics_available"] is True
    assert q40["respondent_count"] == count
    assert len(q40["comments"]) == count
    assert all(comment.endswith(" ") for comment in q40["comments"])


def test_q40_q41_text_is_not_trimmed_rewritten_or_truncated(monkeypatch):
    original_q40 = "  Melhor organização, com o mesmo conteúdo.  "
    original_q41 = "Melhorar a experiência — exatamente como escrito."
    long_text = "x" * 21_000
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", 5), ("Q41", 5)],
        text_answers=[("Q40", original_q40), ("Q41", original_q41), ("Q40", long_text)],
    )

    assert original_q40 in question(payload, "Q40")["comments"]
    assert original_q41 in question(payload, "Q41")["comments"]
    assert long_text in question(payload, "Q40")["comments"]


def test_empty_and_whitespace_text_is_ignored_by_service(monkeypatch):
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", 0), ("Q41", 0), ("Q42", 0)],
        text_answers=[("Q40", ""), ("Q40", "   "), ("Q41", "\t \n"), ("Q42", "  ")],
    )

    assert question(payload, "Q40")["comments"] == []
    assert question(payload, "Q41")["comments"] == []
    assert question(payload, "Q42")["terms"] == []


def test_comments_use_neutral_deterministic_order_and_keep_original_values(monkeypatch):
    originals = ["  Uma mudança. ", "Outra ideia.", "uma mudança."]
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", 5)],
        text_answers=[("Q40", text) for text in originals],
    )

    assert question(payload, "Q40")["comments"] == sorted(
        originals,
        key=lambda text: (" ".join(text.split()).casefold(), text.casefold(), text),
    )


def test_q42_normalizes_trim_case_and_repeated_spaces_and_counts_terms(monkeypatch):
    answers = [
        ("Q42", "Equipe"),
        ("Q42", " equipe "),
        ("Q42", "EQUIPE"),
        ("Q42", "Ambiente"),
        ("Q42", " ambiente  "),
    ]
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q42", 5)],
        text_answers=answers,
    )
    q42 = question(payload, "Q42")

    assert q42["analytics_available"] is True
    assert q42["respondent_count"] == 5
    assert q42["terms"] == [{"term": "equipe", "count": 3}, {"term": "ambiente", "count": 2}]
    assert sum(term["count"] for term in q42["terms"]) == q42["respondent_count"]


def test_q42_orders_terms_by_frequency_then_alphabetically(monkeypatch):
    answers = [("Q42", "equipe") for _ in range(3)] + [("Q42", "ambiente") for _ in range(3)]
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q42", 6)],
        text_answers=answers,
    )

    assert question(payload, "Q42")["terms"] == [
        {"term": "ambiente", "count": 3},
        {"term": "equipe", "count": 3},
    ]


def test_payload_contains_no_platform_or_respondent_identifiers(monkeypatch):
    payload = configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", 5), ("Q41", 5), ("Q42", 5)],
        text_answers=[("Q40", "Comentário"), ("Q41", "Comentário"), ("Q42", "Equipe")],
    )
    serialized = str(payload).lower()
    forbidden = (
        "response_id", "user_id", "email", "feishu", "participation_id", "answer_id",
        "timestamp", "created_at", "ip_address", "session_id", "regional", "segment",
    )

    assert all(field not in serialized for field in forbidden)


def test_logs_never_contain_free_text(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    private = "segredo de texto q40 que nao deve aparecer no log"
    configure_voice_service(
        monkeypatch,
        respondent_counts=[("Q40", 5)],
        text_answers=[("Q40", private)],
    )

    assert "voice analytics requested" in caplog.text
    assert "voice analytics generated" in caplog.text
    assert private not in caplog.text


def test_missing_survey_raises_not_found(monkeypatch):
    configure_voice_service(monkeypatch, current_survey=None)
    monkeypatch.setattr(management_repository, "get_survey_by_code", lambda _db, _code: None)

    with pytest.raises(management_service.ManagementSurveyNotFoundError):
        management_service.get_survey_voice(FakeSession(), "UNKNOWN")


def test_repository_reads_definitions_by_question_code_and_not_internal_ids():
    session = FakeSession()

    management_repository.get_voice_question_definitions(session, 902)

    statement = session.statements[0].compile()
    sql = str(statement).lower()
    params = [item for value in statement.params.values() for item in (value if isinstance(value, list) else [value])]
    assert "survey_questions" in sql
    assert {"Q40", "Q41", "Q42"}.issubset(params)
    assert "survey_questions.id" not in sql
    assert "order by survey_questions.position" in sql


def test_repository_counts_distinct_responders_and_ignores_blank_text():
    session = FakeSession()

    management_repository.get_voice_respondent_counts(session, 902)

    statement = session.statements[0].compile()
    sql = str(statement).lower()
    assert "count(distinct response_answers.response_id)" in sql
    assert "trim(response_answers.text_value)" in sql
    assert "response_answers.text_value is not null" in sql
    assert "users" not in sql
    assert "survey_participation" not in sql
    assert "user_roles" not in sql
    assert "external_auth_codes" not in sql


def test_repository_text_query_selects_only_question_code_and_text_without_ordering():
    session = FakeSession()

    management_repository.get_voice_text_answers(session, 902)

    statement = session.statements[0]
    sql = str(statement.compile()).lower()
    selected_columns = [column.name for column in statement.selected_columns]
    assert selected_columns == ["code", "text_value"]
    assert "response_id" not in sql
    assert "answer_id" not in sql
    assert "order by" not in sql
    assert "users" not in sql
    assert "survey_participation" not in sql


def configure_voice_request(monkeypatch, *, roles=("ADMIN",), current_survey=None, user=None):
    session = FakeSession()
    app.dependency_overrides[get_current_user] = lambda: user or SimpleNamespace(
        id=7, status="ACTIVE", access_type="INTERNAL"
    )
    app.dependency_overrides[get_db_session] = lambda: session
    monkeypatch.setattr(auth_core.identity_repository, "get_user_roles", lambda _db, _user_id: list(roles))
    monkeypatch.setattr(
        management_repository,
        "get_survey_by_code",
        lambda _db, _code: current_survey,
    )
    monkeypatch.setattr(management_repository, "get_voice_question_definitions", lambda _db, _id: QUESTION_DEFINITIONS)
    monkeypatch.setattr(management_repository, "get_voice_respondent_counts", lambda _db, _id: [])
    monkeypatch.setattr(management_repository, "get_voice_text_answers", lambda _db, _id: [])
    return session


@pytest.mark.parametrize("role", ["ADMIN", "MANAGEMENT", "SURVEY_ADMIN"])
def test_management_roles_can_access_voice(monkeypatch, role):
    configure_voice_request(monkeypatch, roles=(role,), current_survey=make_survey())

    response = client.get("/api/management/surveys/CLIMATE_2026/voice")

    assert response.status_code == 200
    assert [item["question_code"] for item in response.json()["questions"]] == ["Q40", "Q41", "Q42"]


@pytest.mark.parametrize("access_type", ["INTERNAL", "EXTERNAL"])
def test_collaborator_only_is_forbidden_from_voice(monkeypatch, access_type):
    configure_voice_request(
        monkeypatch,
        roles=("COLLABORATOR",),
        current_survey=make_survey(),
        user=SimpleNamespace(id=7, status="ACTIVE", access_type=access_type),
    )

    response = client.get("/api/management/surveys/CLIMATE_2026/voice")

    assert response.status_code == 403


def test_voice_requires_authenticated_session():
    app.dependency_overrides[get_db_session] = FakeSession

    response = client.get("/api/management/surveys/CLIMATE_2026/voice")

    assert response.status_code == 401


def test_unknown_survey_returns_404_for_voice(monkeypatch):
    configure_voice_request(monkeypatch)

    response = client.get("/api/management/surveys/UNKNOWN/voice")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


@pytest.mark.parametrize("status", ["DRAFT", "ACTIVE", "CLOSED"])
def test_voice_allows_every_survey_lifecycle_status(monkeypatch, status):
    configure_voice_request(monkeypatch, current_survey=make_survey(status=status))

    response = client.get("/api/management/surveys/CLIMATE_2026/voice")

    assert response.status_code == 200
    assert response.json()["survey_status"] == status


def test_voice_http_schema_has_only_aggregated_content_and_definitions(monkeypatch):
    configure_voice_request(
        monkeypatch,
        current_survey=make_survey(),
    )
    monkeypatch.setattr(
        management_repository,
        "get_voice_respondent_counts",
        lambda _db, _id: [("Q40", 0), ("Q41", 0), ("Q42", 0)],
    )

    response = client.get("/api/management/surveys/CLIMATE_2026/voice")
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) == {"survey_code", "survey_status", "min_group_size", "questions"}
    assert [item["question_code"] for item in payload["questions"]] == ["Q40", "Q41", "Q42"]
    assert payload["questions"][0]["comments"] == []
    assert payload["questions"][2]["terms"] == []
    forbidden = {"user_id", "email", "response_id", "answer_id", "participation_id", "survey_id", "timestamp", "ip", "session_id"}
    assert all(forbidden.isdisjoint(item) for item in payload["questions"])
