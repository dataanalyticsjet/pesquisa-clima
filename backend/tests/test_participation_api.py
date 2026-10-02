from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import surveys as surveys_api
from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.models.participation import SurveyParticipation
from app.repositories import participation_repository
from app.services import participation_service
from app.services.participation_service import ParticipationSurveyNotFoundError


client = TestClient(app)


class FakeSession:
    def scalar(self, statement):
        self.statements.append(statement)
        return None

    def __init__(self):
        self.statements = []


@pytest.fixture(autouse=True)
def clean_client():
    client.cookies.clear()
    app.dependency_overrides.clear()
    yield
    client.cookies.clear()
    app.dependency_overrides.clear()


def fake_user(*, user_id=482, access_type="INTERNAL"):
    return SimpleNamespace(id=user_id, access_type=access_type)


def configure_authenticated_request(monkeypatch, *, user, participation=None, survey=None):
    session = FakeSession()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: session
    monkeypatch.setattr(
        participation_repository,
        "get_survey_by_code",
        lambda actual_session, code: survey
        if code == "CLIMATE_2026"
        else None,
    )
    monkeypatch.setattr(
        participation_repository,
        "get_participation",
        lambda actual_session, survey_id, user_id: participation,
    )
    return session


@pytest.mark.parametrize("access_type", ["INTERNAL", "EXTERNAL"])
def test_authenticated_user_without_participation_is_not_completed(monkeypatch, access_type):
    user = fake_user(access_type=access_type)
    configure_authenticated_request(
        monkeypatch,
        user=user,
        survey=SimpleNamespace(id=9, code="CLIMATE_2026", status="DRAFT"),
    )

    response = client.get("/api/surveys/CLIMATE_2026/participation")

    assert response.status_code == 200
    assert response.json() == {"survey_code": "CLIMATE_2026", "completed": False}


def test_completed_participation_returns_date_and_no_private_identifiers(monkeypatch):
    user = fake_user(access_type="EXTERNAL")
    configure_authenticated_request(
        monkeypatch,
        user=user,
        survey=SimpleNamespace(id=9, code="CLIMATE_2026", status="DRAFT"),
        participation=SimpleNamespace(
            status="COMPLETED", completed_on=date(2026, 9, 30), id=101,
            user_id=user.id, survey_id=9,
        ),
    )

    response = client.get("/api/surveys/CLIMATE_2026/participation")

    assert response.status_code == 200
    assert response.json() == {
        "survey_code": "CLIMATE_2026",
        "completed": True,
        "completed_on": "2026-09-30",
    }
    assert not {"user_id", "survey_id", "participation_id", "response_id", "email", "open_id", "union_id"} & response.json().keys()


def test_participation_lookup_uses_authenticated_user_not_query_user_id(monkeypatch):
    user = fake_user(user_id=482, access_type="EXTERNAL")
    captured = {}

    def get_participation(session, survey_id, user_id):
        captured.update(survey_id=survey_id, user_id=user_id)
        return None

    configure_authenticated_request(
        monkeypatch,
        user=user,
        survey=SimpleNamespace(id=9, code="CLIMATE_2026", status="DRAFT"),
    )
    monkeypatch.setattr(participation_repository, "get_participation", get_participation)

    response = client.get("/api/surveys/CLIMATE_2026/participation?user_id=999")

    assert response.status_code == 200
    assert captured == {"survey_id": 9, "user_id": 482}
    assert response.json() == {"survey_code": "CLIMATE_2026", "completed": False}


def test_unknown_survey_returns_404(monkeypatch):
    configure_authenticated_request(monkeypatch, user=fake_user(), survey=None)

    response = client.get("/api/surveys/DOES_NOT_EXIST/participation")

    assert response.status_code == 404
    assert response.json() == {"detail": "SURVEY_NOT_FOUND"}


def test_participation_endpoint_requires_an_authenticated_session():
    app.dependency_overrides[get_db_session] = FakeSession

    response = client.get("/api/surveys/CLIMATE_2026/participation")

    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHENTICATED"}


def test_draft_survey_participation_status_is_queryable(monkeypatch):
    session = FakeSession()
    draft = SimpleNamespace(id=9, code="CLIMATE_2026", status="DRAFT")
    monkeypatch.setattr(participation_repository, "get_survey_by_code", lambda db, code: draft)
    monkeypatch.setattr(participation_repository, "get_participation", lambda db, survey_id, user_id: None)

    result = participation_service.get_participation_status(session, "CLIMATE_2026", 482)

    assert result == {"survey_code": "CLIMATE_2026", "completed": False}
    assert draft.status == "DRAFT"


def test_service_raises_not_found_for_unknown_survey(monkeypatch):
    monkeypatch.setattr(participation_repository, "get_survey_by_code", lambda db, code: None)

    with pytest.raises(ParticipationSurveyNotFoundError):
        participation_service.get_participation_status(FakeSession(), "UNKNOWN", 482)


def test_repository_query_is_limited_to_participation_table():
    session = FakeSession()

    participation_repository.get_participation(session, survey_id=9, user_id=482)

    assert len(session.statements) == 1
    statement = str(session.statements[0]).lower()
    assert "survey_participation" in statement
    assert "anonymous_responses" not in statement
    assert "response_answers" not in statement
    assert "response_answer_options" not in statement
    assert "anonymous_response_segments" not in statement


def test_participation_model_has_no_response_relationship_or_identifiers():
    columns = set(SurveyParticipation.__table__.columns.keys())
    assert columns == {"id", "survey_id", "user_id", "status", "completed_on"}
    assert "response_id" not in columns and "answer_id" not in columns
    fk_targets = {foreign_key.target_fullname for foreign_key in SurveyParticipation.__table__.foreign_keys}
    assert fk_targets == {"surveys.id", "users.id"}
