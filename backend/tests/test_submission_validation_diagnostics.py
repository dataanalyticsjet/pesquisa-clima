import json
import logging
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.services import survey_submission_service as submission_service
from app.services.survey_submission_service import SurveySubmissionError
from test_survey_submission import (
    FakeOrganizationCatalog, FakeSession, configure_service, submission, valid_answers,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_http_state():
    client.cookies.clear()
    app.dependency_overrides.clear()
    yield
    client.cookies.clear()
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "question_code,replacement,error_code,reason",
    [
        ("Q03", {"option_codes": ["unknown"], "text_value": "private-answer"}, "INVALID_ANSWER", "ANSWER_REPRESENTATION_CONFLICT"),
        ("Q03", {"text_value": ""}, "MISSING_REQUIRED_ANSWER", "CNPJ_REQUIRED_OR_UNKNOWN"),
        ("Q03", {"text_value": "not-a-cnpj"}, "INVALID_ANSWER", "CNPJ_INVALID_FORMAT"),
        ("Q03", {"text_value": "00.000.000/E08G-13"}, "INVALID_ANSWER", "CNPJ_INVALID_CHECK_DIGITS"),
        ("Q01", {"option_codes": ["NOT/APPROVED"]}, "INVALID_OPTION", "INVALID_REGIONAL"),
        ("Q04", {"option_codes": ["1/3"]}, "INVALID_ANSWER", "INVALID_OPTION_CODE_FORMAT"),
        ("Q04", {"text_value": "5"}, "INVALID_ANSWER", "OPTION_CODES_REQUIRED"),
        ("Q04", {"option_codes": []}, "MISSING_REQUIRED_ANSWER", "EMPTY_OPTION_CODES"),
        ("Q04", {"option_codes": ["not-an-option"]}, "INVALID_OPTION", "INVALID_OPTION"),
        ("Q05", {"option_codes": ["A", "B"]}, "INVALID_ANSWER", "SINGLE_OPTION_REQUIRED"),
        ("Q06", {"option_codes": ["none", "A"]}, "EXCLUSIVE_OPTION_CONFLICT", "EXCLUSIVE_OPTION_CONFLICT"),
        ("Q06", {"option_codes": ["A", "A"]}, "INVALID_MULTIPLE_CHOICE", "DUPLICATE_OPTION_CODES"),
        ("Q39", {"text_value": "10"}, "INVALID_ANSWER", "OPTION_CODES_REQUIRED"),
        ("Q39", {"option_codes": ["10 pontos"]}, "INVALID_ANSWER", "INVALID_OPTION_CODE_FORMAT"),
        ("Q40", {"option_codes": ["A"]}, "INVALID_ANSWER", "TEXT_VALUE_REQUIRED"),
        ("Q42", {"option_codes": ["A"]}, "INVALID_ANSWER", "TEXT_VALUE_REQUIRED"),
    ],
)
def test_answer_validation_reports_only_canonical_question_and_reason(
    monkeypatch, question_code, replacement, error_code, reason
):
    session, _, _ = configure_service(monkeypatch)
    answers = [item for item in valid_answers() if item["question_code"] != question_code]
    answers.append({"question_code": question_code, **replacement})
    with pytest.raises(SurveySubmissionError) as error:
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )
    assert error.value.code == error_code
    assert error.value.question_code == question_code
    assert error.value.reason == reason
    assert session.added == [] and session.committed == []
    assert session.commit_count == 0 and session.rollback_count == 1


def configure_http(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=801, access_type="INTERNAL")
    app.dependency_overrides[get_db_session] = lambda: session
    monkeypatch.setattr(submission_service, "organization_catalog_service", FakeOrganizationCatalog())
    return session


def test_http_diagnostic_does_not_expose_cnpj_payload_identity_or_logs(monkeypatch, caplog):
    session = configure_http(monkeypatch)
    answers = valid_answers(cnpj="00.000.000/E08G-13")
    answers.append({"question_code": "Q40", "text_value": "sensitive-test-comment"})
    with caplog.at_level(logging.INFO, logger=submission_service.__name__):
        response = client.post("/api/surveys/CLIMATE_2026/responses", json={"answers": answers})
    assert response.status_code == 422
    assert response.json() == {"detail": {
        "code": "INVALID_ANSWER", "question_code": "Q03", "reason": "CNPJ_INVALID_CHECK_DIGITS"
    }}
    for private_value in ("00.000.000/E08G-13", "sensitive-test-comment", "response_id", "user_id", "email", "text_value", "option_codes"):
        assert private_value not in response.text
        assert private_value not in caplog.text
    assert session.commit_count == 0 and session.rollback_count == 1


@pytest.mark.parametrize("malformed", [
    {"answers": [{"question_code": "Q03", "text_value": {"private": "sensitive-schema-input"}}]},
    {"answers": [{"question_code": "Q03", "option_codes": [{"private": "sensitive-schema-input"}]}]},
    {"answers": [], "private": "sensitive-schema-input"},
    {"answers": [{"question_code": "sensitive schema input", "text_value": "sensitive-schema-input"}]},
])
def test_schema_validation_never_echoes_pydantic_input(monkeypatch, malformed):
    configure_http(monkeypatch)
    response = client.post("/api/surveys/CLIMATE_2026/responses", json=malformed)
    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "INVALID_ANSWER", "reason": "INVALID_REQUEST_FORMAT"}}
    assert "sensitive-schema-input" not in response.text
    assert "input" not in json.dumps(response.json())


def test_unknown_question_is_not_echoed_as_response_content(monkeypatch):
    configure_http(monkeypatch)
    response = client.post("/api/surveys/CLIMATE_2026/responses", json={"answers": valid_answers() + [
        {"question_code": "PRIVATE_RESPONSE_MARKER", "text_value": "private-answer"}
    ]})
    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "INVALID_ANSWER", "reason": "UNKNOWN_QUESTION"}}
    assert "PRIVATE_RESPONSE_MARKER" not in response.text
