import logging
import uuid
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.models.anonymous_responses import (
    AnonymousResponse,
    AnonymousResponseSegment,
    ResponseAnswer,
    ResponseAnswerOption,
)
from app.models.participation import SurveyParticipation
from app.repositories import submission_repository
from app.schemas.responses import SurveySubmissionRequest
from app.services import survey_submission_service as submission_service
from app.services.organization_catalog import OrganizationCatalogService
from app.services.survey_submission_service import SurveySubmissionError


client = TestClient(app)


class FakeSession:
    def __init__(self, *, active=False):
        self.active = active
        self.added = []
        self.committed = []
        self.commit_count = 0
        self.rollback_count = 0
        self._next_answer_id = 101

    def in_transaction(self):
        return self.active

    def begin(self):
        self.active = True
        return self

    def add(self, row):
        self.added.append(row)

    def flush(self):
        for row in self.added:
            if isinstance(row, ResponseAnswer) and row.id is None:
                row.id = self._next_answer_id
                self._next_answer_id += 1

    def commit(self):
        self.commit_count += 1
        self.committed.extend(self.added)
        self.added.clear()
        self.active = False

    def rollback(self):
        self.rollback_count += 1
        self.added.clear()
        self.active = False


class FakeOrganizationCatalog(OrganizationCatalogService):
    def __init__(self, *, available=True, valid=True):
        self.available = available
        self.valid = valid
        self.calls = []

    def validate_selection(
        self,
        option_source,
        option_code,
        *,
        regional_code=None,
        base_code=None,
    ):
        self.calls.append((option_source, option_code, regional_code, base_code))
        if not self.available:
            return None
        if not self.valid:
            return False
        expected = {
            ("ORG_REGIONAL", "R1", None, None),
            ("ORG_BASE", "B1", "R1", None),
        }
        return (option_source, option_code, regional_code, base_code) in expected


@pytest.fixture(autouse=True)
def clear_client_state():
    client.cookies.clear()
    app.dependency_overrides.clear()
    yield
    client.cookies.clear()
    app.dependency_overrides.clear()


def survey(*, status="ACTIVE", survey_id=12, code="CLIMATE_2026"):
    return SimpleNamespace(id=survey_id, code=code, status=status)


def question(number, question_type, *, required=True, option_source="STATIC"):
    return SimpleNamespace(
        id=number,
        survey_id=12,
        question_number=number,
        code=f"Q{number:02d}",
        question_type=question_type,
        required=required,
        option_source=option_source,
    )


def option(question_id, code, *, exclusive=False):
    return SimpleNamespace(
        id=question_id * 1000 + sum(ord(character) for character in code),
        question_id=question_id,
        code=code,
        label="Não sei informar" if code == "unknown" else code,
        is_exclusive=exclusive,
    )


def definition():
    questions = [
        question(1, "SELECT", option_source="ORG_REGIONAL"),
        question(2, "SELECT", option_source="ORG_BASE"),
        question(3, "SELECT", option_source="ORG_CNPJ"),
        question(4, "LIKERT"),
        question(5, "SINGLE_CHOICE"),
        question(6, "MULTIPLE_CHOICE"),
        question(39, "NPS"),
        question(40, "TEXTAREA", required=False),
        question(42, "SHORT_TEXT", required=False),
    ]
    options = [
        option(3, "unknown"),
        option(4, "1"), option(4, "5"),
        option(5, "A"), option(5, "B"),
        option(6, "A"), option(6, "B"), option(6, "none", exclusive=True),
        *[option(39, f"nps-{score}") for score in range(11)],
    ]
    return questions, options


def valid_answers(*, cnpj="unknown", multi=None):
    q3 = (
        {"question_code": "Q03", "option_codes": ["unknown"]}
        if cnpj == "unknown"
        else {"question_code": "Q03", "text_value": cnpj}
    )
    return [
        {"question_code": "Q01", "option_codes": ["R1"]},
        {"question_code": "Q02", "option_codes": ["B1"]},
        q3,
        {"question_code": "Q04", "option_codes": ["5"]},
        {"question_code": "Q05", "option_codes": ["A"]},
        {"question_code": "Q06", "option_codes": multi or ["A", "B"]},
        {"question_code": "Q39", "option_codes": ["nps-10"]},
    ]


def submission(answers=None, **extra):
    return SurveySubmissionRequest.model_validate({"answers": valid_answers() if answers is None else answers, **extra})


def configure_service(monkeypatch, *, current_survey=None, current_questions=None, current_options=None, existing=None):
    session = FakeSession(active=True)
    questions, options = definition()
    monkeypatch.setattr(submission_repository, "get_survey_by_code", lambda db, code: current_survey or survey())
    monkeypatch.setattr(submission_repository, "get_participation", lambda db, sid, uid: existing)
    monkeypatch.setattr(submission_repository, "get_questions_by_survey", lambda db, sid: questions if current_questions is None else current_questions)
    monkeypatch.setattr(submission_repository, "get_options_by_question_ids", lambda db, ids: options if current_options is None else current_options)
    return session, questions, options


def test_privacy_models_match_anonymous_schema_without_identity_links():
    assert set(AnonymousResponse.__table__.columns.keys()) == {"response_id", "survey_id"}
    assert set(ResponseAnswer.__table__.columns.keys()) == {"id", "response_id", "survey_id", "question_id", "text_value"}
    assert set(ResponseAnswerOption.__table__.columns.keys()) == {"answer_id", "question_id", "option_id"}
    assert set(AnonymousResponseSegment.__table__.columns.keys()) == {"response_id", "segment_type", "segment_code"}
    assert "user_id" not in AnonymousResponse.__table__.columns
    assert "participation_id" not in AnonymousResponse.__table__.columns
    assert "response_id" not in SurveyParticipation.__table__.columns
    assert "created_at" not in AnonymousResponse.__table__.columns
    assert "submitted_at" not in AnonymousResponse.__table__.columns


def test_submission_repository_never_joins_identity_to_anonymous_answers():
    class QueryRecorder:
        def __init__(self):
            self.statements = []

        def scalar(self, statement):
            self.statements.append(str(statement).lower())
            return None

        def scalars(self, statement):
            self.statements.append(str(statement).lower())
            return SimpleNamespace(all=lambda: [])

    db = QueryRecorder()
    submission_repository.get_participation(db, 12, 801)
    for statement in db.statements:
        assert "join" not in statement
        assert "anonymous_responses" not in statement
        assert "response_answers" not in statement


def test_valid_active_submission_writes_anonymous_answers_segments_then_participation(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    catalog = FakeOrganizationCatalog()
    response_uuid = uuid.uuid4()

    result = submission_service.submit_survey(
        session,
        "CLIMATE_2026",
        801,
        submission(),
        organization_catalog=catalog,
        response_id_factory=lambda: response_uuid,
    )

    assert result == {"submitted": True}
    assert session.commit_count == 1 and session.rollback_count == 0
    rows = session.committed
    anonymous = next(row for row in rows if isinstance(row, AnonymousResponse))
    participation = next(row for row in rows if isinstance(row, SurveyParticipation))
    assert anonymous.response_id == str(response_uuid)
    assert uuid.UUID(anonymous.response_id).version == 4
    assert anonymous.response_id != str(801)
    assert participation.user_id == 801 and participation.status == "COMPLETED"
    assert participation.completed_on == date.today()
    assert not hasattr(anonymous, "user_id") and not hasattr(anonymous, "participation_id")
    assert {row.segment_type for row in rows if isinstance(row, AnonymousResponseSegment)} == {"REGIONAL", "BASE"}
    assert "AREA" not in {row.segment_type for row in rows if isinstance(row, AnonymousResponseSegment)}


def test_q3_unknown_is_saved_as_static_option_without_cnpj_segment(monkeypatch):
    session, _, _ = configure_service(monkeypatch)

    submission_service.submit_survey(
        session, "CLIMATE_2026", 801, submission(), organization_catalog=FakeOrganizationCatalog()
    )

    rows = session.committed
    q3_answer = next(row for row in rows if isinstance(row, ResponseAnswer) and row.question_id == 3)
    assert q3_answer.text_value is None
    q3_option = next(row for row in rows if isinstance(row, ResponseAnswerOption) and row.question_id == 3)
    assert q3_option.option_id == option(3, "unknown").id
    assert not any(isinstance(row, AnonymousResponseSegment) and row.segment_type == "CNPJ" for row in rows)


def test_validated_org_codes_are_text_values_and_segments_are_anonymous(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    catalog = FakeOrganizationCatalog()

    submission_service.submit_survey(
        session,
        "CLIMATE_2026",
        801,
        submission(valid_answers(cnpj="00.000.000/E08G-12")),
        organization_catalog=catalog,
    )

    rows = session.committed
    org_answers = {row.question_id: row for row in rows if isinstance(row, ResponseAnswer) and row.question_id in {1, 2, 3}}
    assert {key: value.text_value for key, value in org_answers.items()} == {1: "R1", 2: "B1", 3: "00000000E08G12"}
    assert not any(isinstance(row, ResponseAnswerOption) and row.question_id in {1, 2, 3} for row in rows)
    assert {row.segment_type: row.segment_code for row in rows if isinstance(row, AnonymousResponseSegment)} == {
        "REGIONAL": "R1", "BASE": "B1", "CNPJ": "00000000E08G12"
    }
    assert catalog.calls == [
        ("ORG_REGIONAL", "R1", None, None),
        ("ORG_BASE", "B1", "R1", None),
    ]



def test_invalid_cnpj_format_and_check_digits_are_rejected(monkeypatch):
    for value in ("123", "00.000.000/E08G-13", "00.000.000/E08@-12", "00000000E08GAB"):
        session, _, _ = configure_service(monkeypatch)
        with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
            submission_service.submit_survey(
                session,
                "CLIMATE_2026",
                801,
                submission(valid_answers(cnpj=value)),
                organization_catalog=FakeOrganizationCatalog(),
            )
        assert session.commit_count == 0 and session.rollback_count == 1


def test_numeric_cnpj_is_normalized_and_segmented(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    submission_service.submit_survey(
        session, "CLIMATE_2026", 801,
        submission(valid_answers(cnpj="11.222.333/0001-81")),
        organization_catalog=FakeOrganizationCatalog(),
    )
    rows = session.committed
    q3 = next(row for row in rows if isinstance(row, ResponseAnswer) and row.question_id == 3)
    assert q3.text_value == "11222333000181"
    cnpj_segment = next(row for row in rows if isinstance(row, AnonymousResponseSegment) and row.segment_type == "CNPJ")
    assert cnpj_segment.segment_code == "11222333000181"


def test_unknown_and_cnpj_cannot_be_submitted_together(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers()
    answers[2] = {"question_code": "Q03", "option_codes": ["unknown"], "text_value": "11222333000181"}
    with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )
    assert session.added == [] and session.rollback_count == 1

def test_organization_hierarchy_validation_does_not_depend_on_payload_order(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers(cnpj="00.000.000/E08G-12")

    submission_service.submit_survey(
        session,
        "CLIMATE_2026",
        801,
        submission(list(reversed(answers))),
        organization_catalog=FakeOrganizationCatalog(),
    )

    assert session.commit_count == 1


def test_cnpj_is_validated_without_catalog_lookup(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    catalog = FakeOrganizationCatalog()

    submission_service.submit_survey(
        session,
        "CLIMATE_2026",
        801,
        submission(valid_answers(cnpj="00.000.000/E08G-12")),
        organization_catalog=catalog,
    )

    assert [call[0] for call in catalog.calls] == ["ORG_REGIONAL", "ORG_BASE"]


def test_wrong_organization_hierarchy_is_invalid_option(monkeypatch):
    session, _, _ = configure_service(monkeypatch)

    with pytest.raises(SurveySubmissionError, match="INVALID_OPTION"):
        submission_service.submit_survey(
            session,
            "CLIMATE_2026",
            801,
            submission(),
            organization_catalog=FakeOrganizationCatalog(valid=False),
        )

    assert session.added == [] and session.rollback_count == 1


def test_missing_survey_is_controlled(monkeypatch):
    session, _, _ = configure_service(monkeypatch, current_survey=None)
    monkeypatch.setattr(submission_repository, "get_survey_by_code", lambda db, code: None)

    with pytest.raises(SurveySubmissionError, match="SURVEY_NOT_FOUND"):
        submission_service.submit_survey(session, "MISSING", 801, submission())

    assert session.commit_count == 0 and session.rollback_count == 1


def test_draft_survey_is_rejected(monkeypatch):
    session, _, _ = configure_service(monkeypatch, current_survey=survey(status="DRAFT"))

    with pytest.raises(SurveySubmissionError, match="SURVEY_NOT_ACTIVE"):
        submission_service.submit_survey(session, "CLIMATE_2026", 801, submission())

    assert session.added == [] and session.commit_count == 0


def test_existing_participation_is_duplicate_conflict(monkeypatch):
    session, _, _ = configure_service(monkeypatch, existing=SimpleNamespace(status="COMPLETED"))

    with pytest.raises(SurveySubmissionError, match="SURVEY_ALREADY_COMPLETED"):
        submission_service.submit_survey(session, "CLIMATE_2026", 801, submission())

    assert session.added == [] and session.commit_count == 0


def test_database_unique_race_rolls_back_all_anonymous_rows(monkeypatch):
    session, _, _ = configure_service(monkeypatch)

    def collide(db, row):
        raise IntegrityError(
            "insert participation",
            {},
            Exception("Duplicate entry for key 'uq_survey_participation_survey_user'"),
        )

    monkeypatch.setattr(submission_repository, "add_survey_participation", collide)

    with pytest.raises(SurveySubmissionError, match="SURVEY_ALREADY_COMPLETED"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(), organization_catalog=FakeOrganizationCatalog()
        )

    assert session.added == [] and session.committed == []
    assert session.commit_count == 0 and session.rollback_count == 1


def test_any_persistence_failure_rolls_back_instead_of_orphaning_response(monkeypatch):
    session, _, _ = configure_service(monkeypatch)

    def fail_segment(db, segment):
        raise RuntimeError("private internal failure")

    monkeypatch.setattr(submission_repository, "add_anonymous_response_segment", fail_segment)

    with pytest.raises(SurveySubmissionError, match="SUBMISSION_UNAVAILABLE"):
        submission_service.submit_survey(
            session,
            "CLIMATE_2026",
            801,
            submission(valid_answers(cnpj="00.000.000/E08G-12")),
            organization_catalog=FakeOrganizationCatalog(),
        )

    assert session.added == [] and session.committed == []
    assert session.commit_count == 0 and session.rollback_count == 1


def test_missing_required_question_uses_database_required_flag(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = [item for item in valid_answers() if item["question_code"] != "Q04"]

    with pytest.raises(SurveySubmissionError, match="MISSING_REQUIRED_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )


def test_unknown_question_and_unknown_option_are_rejected(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers() + [{"question_code": "Q99", "option_codes": ["x"]}]
    with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )

    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers()
    answers[3] = {"question_code": "Q04", "option_codes": ["not-an-option"]}
    with pytest.raises(SurveySubmissionError, match="INVALID_OPTION"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )


def test_option_belonging_to_another_question_is_rejected(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers()
    answers[3] = {"question_code": "Q04", "option_codes": ["A"]}

    with pytest.raises(SurveySubmissionError, match="INVALID_OPTION"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )


def test_single_choice_rejects_multiple_and_multiple_choice_accepts_valid_options(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers()
    answers[4] = {"question_code": "Q05", "option_codes": ["A", "B"]}
    with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )

    session, _, _ = configure_service(monkeypatch)
    submission_service.submit_survey(
        session, "CLIMATE_2026", 801, submission(), organization_catalog=FakeOrganizationCatalog()
    )
    multi_answer = next(row for row in session.committed if isinstance(row, ResponseAnswer) and row.question_id == 6)
    selected = [row for row in session.committed if isinstance(row, ResponseAnswerOption) and row.answer_id == multi_answer.id]
    assert len(selected) == 2


def test_exclusive_option_is_valid_alone_and_conflicts_with_other_options(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers(multi=["none"])
    submission_service.submit_survey(
        session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
    )
    assert sum(
        isinstance(row, ResponseAnswerOption) and row.question_id == 6 for row in session.committed
    ) == 1

    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers(multi=["none", "A"])
    with pytest.raises(SurveySubmissionError, match="EXCLUSIVE_OPTION_CONFLICT"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )


def test_likert_and_nps_use_option_codes_from_their_own_question(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    submission_service.submit_survey(
        session, "CLIMATE_2026", 801, submission(), organization_catalog=FakeOrganizationCatalog()
    )
    selected = [row for row in session.committed if isinstance(row, ResponseAnswerOption)]
    assert any(row.question_id == 4 and row.option_id == option(4, "5").id for row in selected)
    assert any(row.question_id == 39 and row.option_id == option(39, "nps-10").id for row in selected)


def test_optional_textarea_and_short_text_may_be_omitted(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    submission_service.submit_survey(
        session, "CLIMATE_2026", 801, submission(), organization_catalog=FakeOrganizationCatalog()
    )
    assert not any(isinstance(row, ResponseAnswer) and row.question_id in {40, 42} for row in session.committed)


def test_text_answers_reject_options_and_option_questions_reject_text(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers() + [{"question_code": "Q40", "option_codes": ["A"]}]
    with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )

    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers()
    answers[3] = {"question_code": "Q04", "text_value": "5"}
    with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )


def test_text_answer_is_preserved_but_never_written_to_logs(monkeypatch, caplog):
    session, _, _ = configure_service(monkeypatch)
    text_value = "  Texto confidencial do respondente \n"
    answers = valid_answers() + [{"question_code": "Q40", "text_value": text_value}]
    with caplog.at_level(logging.INFO, logger=submission_service.__name__):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )

    text_answer = next(row for row in session.committed if isinstance(row, ResponseAnswer) and row.question_id == 40)
    assert text_answer.text_value == text_value
    assert text_value not in caplog.text


def test_http_submission_requires_session_returns_no_response_id_and_rejects_private_fields(monkeypatch):
    app.dependency_overrides[get_db_session] = lambda: FakeSession()
    unauthenticated = client.post("/api/surveys/CLIMATE_2026/responses", json={"answers": []})
    assert unauthenticated.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=801, access_type="EXTERNAL")
    monkeypatch.setattr(submission_repository, "get_survey_by_code", lambda db, code: survey())
    payload = {"answers": valid_answers(), "user_id": 999}
    private_field = client.post("/api/surveys/CLIMATE_2026/responses", json=payload)
    assert private_field.status_code == 422

    questions, options = definition()
    monkeypatch.setattr(submission_repository, "get_participation", lambda db, sid, uid: None)
    monkeypatch.setattr(submission_repository, "get_questions_by_survey", lambda db, sid: questions)
    monkeypatch.setattr(submission_repository, "get_options_by_question_ids", lambda db, ids: options)
    monkeypatch.setattr(submission_service, "organization_catalog_service", FakeOrganizationCatalog())
    response = client.post(
        "/api/surveys/CLIMATE_2026/responses", json={"answers": valid_answers()}
    )

    assert response.status_code == 201
    assert response.json() == {"submitted": True}
    assert "response_id" not in response.json()
    assert "user_id" not in response.json()


def test_http_duplicate_participation_returns_409(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=801, access_type="INTERNAL")
    app.dependency_overrides[get_db_session] = FakeSession
    monkeypatch.setattr(submission_repository, "get_survey_by_code", lambda db, code: survey())
    monkeypatch.setattr(
        submission_repository,
        "get_participation",
        lambda db, sid, uid: SimpleNamespace(status="COMPLETED"),
    )

    response = client.post(
        "/api/surveys/CLIMATE_2026/responses", json={"answers": valid_answers()}
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "SURVEY_ALREADY_COMPLETED"}


def test_duplicate_request_question_is_invalid(monkeypatch):
    session, _, _ = configure_service(monkeypatch)
    answers = valid_answers() + [valid_answers()[0]]

    with pytest.raises(SurveySubmissionError, match="INVALID_ANSWER"):
        submission_service.submit_survey(
            session, "CLIMATE_2026", 801, submission(answers), organization_catalog=FakeOrganizationCatalog()
        )


def test_request_schema_forbids_ids_and_identity_fields():
    with pytest.raises(Exception):
        SurveySubmissionRequest.model_validate(
            {"answers": [], "email": "person@example.test", "participation_id": 44}
        )
