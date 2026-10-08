from types import SimpleNamespace as Row

import pytest
from fastapi.testclient import TestClient

from app.api import surveys as surveys_api
from app.main import app
from app.repositories.survey_repository import SurveyReadData
from app.services import survey_service
from app.services.survey_service import SurveyNotActiveError


client = TestClient(app)


def make_option(question_id, code, label, position, score_value=None, is_exclusive=False):
    return Row(
        id=position + question_id * 100,
        question_id=question_id,
        code=code,
        label=label,
        position=position,
        score_value=score_value,
        is_exclusive=is_exclusive,
    )


def make_question(question_number, section_id, option_source="STATIC", required=True, question_type="SINGLE_CHOICE"):
    return Row(
        id=question_number,
        survey_id=7,
        section_id=section_id,
        question_number=question_number,
        code=f"Q{question_number:02d}",
        question_type=question_type,
        text=f"Pergunta {question_number}",
        helper_text=None,
        placeholder=None,
        low_label=None,
        high_label=None,
        required=required,
        position=question_number,
        analysis_role="CATEGORY",
        option_source=option_source,
    )


@pytest.fixture
def read_data():
    survey = Row(
        id=7,
        code="CLIMATE_2026",
        title="Pesquisa de Clima Organizacional 2026",
        intro_text="Introdução",
        completion_text="Obrigada por participar!",
        status="DRAFT",
        version=1,
    )
    sections = [
        Row(id=2, survey_id=7, code="SEGUNDA", title="Segunda", position=2, analysis_type="SCORE"),
        Row(id=1, survey_id=7, code="PRIMEIRA", title="Primeira", position=1, analysis_type="SEGMENT"),
    ]
    questions = [
        make_question(2, 1, "ORG_BASE"),
        make_question(1, 1, "ORG_REGIONAL"),
        make_question(3, 1, "STATIC", question_type="SINGLE_CHOICE"),
        make_question(33, 2, "STATIC", question_type="LIKERT"),
        make_question(6, 2, "STATIC", question_type="MULTIPLE_CHOICE"),
        make_question(39, 2, "STATIC", question_type="NPS"),
        make_question(40, 2, "STATIC", required=False, question_type="TEXTAREA"),
        make_question(41, 2, "STATIC", required=False, question_type="TEXTAREA"),
        make_question(42, 2, "STATIC", required=False, question_type="SHORT_TEXT"),
    ]
    questions[3].question_number = 0
    options = [
        make_option(1, "demo-regional", "Regional fictícia", 1),
        make_option(2, "demo-base", "Base fictícia", 1),
        make_option(3, "OPERATIONAL", "Operacional", 1),
        make_option(3, "ADMINISTRATIVE", "Administrativo", 2),
        make_option(3, "unknown", "Não sei informar", 65535),
        make_option(6, "exclusive", "Não identifico necessidade de melhoria", 9, is_exclusive=True),
        *[make_option(39, f"nps-{score}", str(score), score + 1, score_value=score) for score in reversed(range(11))],
    ]
    return SurveyReadData(survey=survey, sections=sections, questions=questions, options=options)


def test_get_survey_returns_definition_and_allows_draft(monkeypatch):
    expected = {
        "code": "CLIMATE_2026",
        "title": "Pesquisa de Clima Organizacional 2026",
        "intro_text": "Introdução",
        "completion_text": "Obrigada por participar!",
        "status": "DRAFT",
        "version": 1,
        "sections": [],
    }
    monkeypatch.setattr(surveys_api, "get_survey_definition", lambda code, require_active=False: expected)

    response = client.get("/api/surveys/CLIMATE_2026")

    assert response.status_code == 200
    assert response.json() == expected


def test_get_survey_returns_controlled_404_when_missing(monkeypatch):
    monkeypatch.setattr(surveys_api, "get_survey_definition", lambda code, require_active=False: None)

    response = client.get("/api/surveys/DOES_NOT_EXIST")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


def test_service_orders_definition_and_filters_organizational_options(monkeypatch, read_data):
    monkeypatch.setattr(survey_service, "get_survey_by_code", lambda code: read_data)

    result = survey_service.get_survey_definition("CLIMATE_2026")

    assert result["status"] == "DRAFT"
    assert [section["position"] for section in result["sections"]] == [1, 2]
    first_section = result["sections"][0]
    assert [question["code"] for question in first_section["questions"]] == ["Q01", "Q02", "Q03"]
    first_questions = {question["code"]: question for question in first_section["questions"]}
    second_section = result["sections"][1]
    assert [question["code"] for question in second_section["questions"]] == ["Q06", "Q39", "Q40", "Q41", "Q42"]
    assert all(question["code"] != "Q33" for section in result["sections"] for question in section["questions"])
    second_questions = {question["code"]: question for question in second_section["questions"]}

    assert all(isinstance(question["required"], bool) for section in result["sections"] for question in section["questions"])
    assert first_questions["Q01"]["options"] == []
    assert first_questions["Q02"]["options"] == []
    assert first_questions["Q03"]["options"] == [
        {"code": "OPERATIONAL", "label": "Operacional", "position": 1, "score_value": None, "is_exclusive": False},
        {"code": "ADMINISTRATIVE", "label": "Administrativo", "position": 2, "score_value": None, "is_exclusive": False},
    ]
    assert second_questions["Q06"]["options"][0]["is_exclusive"] is True
    assert [option["score_value"] for option in second_questions["Q39"]["options"]] == list(range(11))
    assert all(second_questions[f"Q{number:02d}"]["required"] is False for number in (40, 41, 42))
    assert [option["position"] for option in second_questions["Q39"]["options"]] == list(range(1, 12))


def test_service_returns_none_for_unknown_survey(monkeypatch):
    monkeypatch.setattr(survey_service, "get_survey_by_code", lambda code: None)

    assert survey_service.get_survey_definition("UNKNOWN") is None


def test_service_can_require_active_for_future_public_use(monkeypatch, read_data):
    monkeypatch.setattr(survey_service, "get_survey_by_code", lambda code: read_data)

    with pytest.raises(SurveyNotActiveError):
        survey_service.get_survey_definition("CLIMATE_2026", require_active=True)
