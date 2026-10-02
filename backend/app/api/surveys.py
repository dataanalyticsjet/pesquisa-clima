from fastapi import APIRouter, HTTPException

from app.schemas.survey import SurveyDefinitionResponse
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
