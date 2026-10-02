from datetime import date

from sqlalchemy.orm import Session

from app.repositories import participation_repository


class ParticipationSurveyNotFoundError(Exception):
    pass


def get_participation_status(
    session: Session, survey_code: str, user_id: int
) -> dict[str, str | bool | date]:
    survey = participation_repository.get_survey_by_code(session, survey_code)
    if survey is None:
        raise ParticipationSurveyNotFoundError

    participation = participation_repository.get_participation(
        session, survey.id, user_id
    )
    if participation is None:
        return {"survey_code": survey.code, "completed": False}

    return {
        "survey_code": survey.code,
        "completed": participation.status == "COMPLETED",
        "completed_on": participation.completed_on,
    }
