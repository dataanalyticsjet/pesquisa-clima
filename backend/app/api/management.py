from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_db_session, require_management_access
from app.models.identity import User
from app.schemas.management import (
    ManagementSurveyOverviewResponse,
    ManagementSurveyPillarsResponse,
)
from app.services.management_service import (
    ManagementSurveyNotFoundError,
    get_survey_overview,
    get_survey_pillars,
)


router = APIRouter(prefix="/api/management/surveys", tags=["management"])


@router.get(
    "/{survey_code}/overview",
    response_model=ManagementSurveyOverviewResponse,
)
def read_survey_overview(
    survey_code: str,
    _user: User = Depends(require_management_access),
    session: Session = Depends(get_db_session),
):
    try:
        return get_survey_overview(session, survey_code)
    except ManagementSurveyNotFoundError:
        raise HTTPException(status_code=404, detail="SURVEY_NOT_FOUND") from None


@router.get(
    "/{survey_code}/pillars",
    response_model=ManagementSurveyPillarsResponse,
)
def read_survey_pillars(
    survey_code: str,
    _user: User = Depends(require_management_access),
    session: Session = Depends(get_db_session),
):
    try:
        return get_survey_pillars(session, survey_code)
    except ManagementSurveyNotFoundError:
        raise HTTPException(status_code=404, detail="SURVEY_NOT_FOUND") from None
