from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.participation import SurveyParticipation
from app.models.survey import Survey


def get_survey_by_code(session: Session, survey_code: str) -> Survey | None:
    return session.scalar(select(Survey).where(Survey.code == survey_code))


def get_participation(
    session: Session, survey_id: int, user_id: int
) -> SurveyParticipation | None:
    statement = select(SurveyParticipation).where(
        SurveyParticipation.survey_id == survey_id,
        SurveyParticipation.user_id == user_id,
    )
    return session.scalar(statement)
