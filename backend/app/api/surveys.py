from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_db_session
from app.models.identity import User
from app.schemas.participation import ParticipationStatusResponse
from app.schemas.survey import SurveyDefinitionResponse
from app.services.participation_service import (
    ParticipationSurveyNotFoundError,
    get_participation_status,
)
from app.services.survey_service import SurveyNotActiveError, get_survey_definition


router = APIRouter(prefix="/api/surveys", tags=["surveys"])


@router.get("/{survey_code}", response_model=SurveyDefinitionResponse)
def read_survey(survey_code: str):
    try:
        survey = get_survey_definition(survey_code, require_active=False)
    except SurveyNotActiveError:
        raise HTTPException(status_code=404, detail="SURVEY_NOT_FOUND") from None
    except Exception:
        raise HTTPException(status_code=503, detail="SURVEY_UNAVAILABLE") from None

    if survey is None:
        raise HTTPException(status_code=404, detail="SURVEY_NOT_FOUND")

    return survey


@router.get(
    "/{survey_code}/participation",
    response_model=ParticipationStatusResponse,
    response_model_exclude_none=True,
)
def read_participation(
    survey_code: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    try:
        return get_participation_status(session, survey_code, user.id)
    except ParticipationSurveyNotFoundError:
        raise HTTPException(status_code=404, detail="SURVEY_NOT_FOUND") from None
