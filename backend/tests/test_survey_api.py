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


def test_service_keeps_stable_codes_when_visual_numbers_and_sections_change(monkeypatch, read_data):
    leadership = Row(id=4, survey_id=7, code="LIDERANCA", title="Liderança", position=4, analysis_type="SCORE")
    environment = Row(id=5, survey_id=7, code="AMBIENTE", title="Ambiente", position=5, analysis_type="SCORE")
    ethics = Row(id=6, survey_id=7, code="ETICA", title="Ética", position=6, analysis_type="SCORE")
    q24 = make_question(16, 4, question_type="LIKERT")
    q24.id = 24
    q24.code = "Q24"
    q24.text = "Percebo que minha liderança atua de forma ética e coerente com as regras da empresa."
    q24.position = 6
    q24.analysis_role = "SCORE"

    q16 = make_question(17, 5, question_type="LIKERT")
    q16.id, q16.code, q16.position, q16.analysis_role = 16, "Q16", 1, "SCORE"
    q21 = make_question(22, 6, question_type="LIKERT")
    q21.id, q21.code, q21.position, q21.analysis_role = 21, "Q21", 1, "SCORE"
    q22 = make_question(23, 6, question_type="LIKERT")
    q22.id, q22.code, q22.position, q22.analysis_role = 22, "Q22", 2, "SCORE"
    q23 = make_question(24, 6, question_type="LIKERT")
    q23.id = 23
    q23.code = "Q23"
    q23.text = "Sinto segurança para realizar um relato ou denúncia sem medo de sofrer retaliação ou consequências negativas."
    q23.position = 3
    q23.analysis_role = "SCORE"
    read_data.sections.extend([leadership, environment, ethics])
    read_data.questions.extend([q24, q16, q21, q22, q23])
    monkeypatch.setattr(survey_service, "get_survey_by_code", lambda code: read_data)

    result = survey_service.get_survey_definition("CLIMATE_2026")
    by_section = {section["code"]: section for section in result["sections"]}

    assert [
        (question["code"], question["question_number"])
        for question in by_section["LIDERANCA"]["questions"]
    ] == [("Q24", 16)]
    assert [
        (question["code"], question["question_number"])
        for question in by_section["AMBIENTE"]["questions"]
    ] == [("Q16", 17)]
    assert [(question["code"], question["question_number"]) for question in by_section["ETICA"]["questions"]] == [
        ("Q21", 22), ("Q22", 23), ("Q23", 24)
    ]

def test_service_returns_none_for_unknown_survey(monkeypatch):
    monkeypatch.setattr(survey_service, "get_survey_by_code", lambda code: None)

    assert survey_service.get_survey_definition("UNKNOWN") is None


def test_service_can_require_active_for_future_public_use(monkeypatch, read_data):
    monkeypatch.setattr(survey_service, "get_survey_by_code", lambda code: read_data)

    with pytest.raises(SurveyNotActiveError):
        survey_service.get_survey_definition("CLIMATE_2026", require_active=True)
