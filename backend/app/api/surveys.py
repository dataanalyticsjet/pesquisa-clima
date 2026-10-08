from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_db_session
from app.api.params import SurveyCodePath
from app.models.identity import User
from app.schemas.participation import ParticipationStatusResponse
from app.schemas.responses import SurveySubmissionRequest, SurveySubmissionResponse
from app.schemas.survey import SurveyDefinitionResponse
from app.services.participation_service import (
    ParticipationSurveyNotFoundError,
    get_participation_status,
)
from app.services.survey_submission_service import SurveySubmissionError, submit_survey
from app.services.survey_service import SurveyNotActiveError, get_survey_definition


class SurveySubmissionRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        if "POST" not in self.methods or not self.path.endswith("/{survey_code}/responses"):
            return handler

        async def safe_submission_handler(request: Request):
            try:
                return await handler(request)
            except RequestValidationError:
                # Pydantic's default error includes raw input. Never echo submission content.
                raise HTTPException(
                    status_code=422,
                    detail={"code": "INVALID_ANSWER", "reason": "INVALID_REQUEST_FORMAT"},
                ) from None

        return safe_submission_handler


router = APIRouter(prefix="/api/surveys", tags=["surveys"], route_class=SurveySubmissionRoute)


@router.get("/{survey_code}", response_model=SurveyDefinitionResponse)
def read_survey(survey_code: SurveyCodePath):
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
    survey_code: SurveyCodePath,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    try:
        return get_participation_status(session, survey_code, user.id)
    except ParticipationSurveyNotFoundError:
        raise HTTPException(status_code=404, detail="SURVEY_NOT_FOUND") from None


@router.post(
    "/{survey_code}/responses",
    response_model=SurveySubmissionResponse,
    status_code=201,
)
def submit_survey_responses(
    survey_code: SurveyCodePath,
    body: SurveySubmissionRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    status_by_error = {
        "SURVEY_NOT_FOUND": 404,
        "SURVEY_NOT_ACTIVE": 409,
        "SURVEY_ALREADY_COMPLETED": 409,
        "MISSING_REQUIRED_ANSWER": 422,
        "INVALID_ANSWER": 422,
        "INVALID_OPTION": 422,
        "INVALID_MULTIPLE_CHOICE": 422,
        "EXCLUSIVE_OPTION_CONFLICT": 422,
        "ORGANIZATION_CATALOG_UNAVAILABLE": 503,
        "SUBMISSION_UNAVAILABLE": 503,
    }
    try:
        return submit_survey(session, survey_code, user.id, body)
    except SurveySubmissionError as error:
        status_code = status_by_error.get(error.code, 503)
        if error.reason is None:
            detail = error.code
        else:
            detail = {"code": error.code, "reason": error.reason}
            if error.question_code is not None:
                detail["question_code"] = error.question_code
        raise HTTPException(status_code=status_code, detail=detail) from None
