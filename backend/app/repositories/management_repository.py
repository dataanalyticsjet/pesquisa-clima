from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from app.models.anonymous_responses import (
    AnonymousResponse,
    ResponseAnswer,
    ResponseAnswerOption,
)
from app.models.participation import SurveyParticipation
from app.models.survey import Survey, SurveyQuestion, SurveyQuestionOption


def get_survey_by_code(session: Session, survey_code: str) -> Survey | None:
    return session.scalar(select(Survey).where(Survey.code == survey_code))


def count_completed_participations(session: Session, survey_id: int) -> int:
    statement = (
        select(func.count())
        .select_from(SurveyParticipation)
        .where(
            SurveyParticipation.survey_id == survey_id,
            SurveyParticipation.status == "COMPLETED",
        )
    )
    return int(session.scalar(statement) or 0)


def count_anonymous_responses(session: Session, survey_id: int) -> int:
    statement = (
        select(func.count())
        .select_from(AnonymousResponse)
        .where(AnonymousResponse.survey_id == survey_id)
    )
    return int(session.scalar(statement) or 0)


def get_q39_score_counts(session: Session, survey_id: int) -> list[tuple[int, int]]:
    """Aggregate Q39 scores entirely within the anonymous response domain."""
    statement = (
        select(
            SurveyQuestionOption.score_value,
            func.count(distinct(ResponseAnswer.response_id)),
        )
        .select_from(ResponseAnswer)
        .join(
            SurveyQuestion,
            and_(
                SurveyQuestion.id == ResponseAnswer.question_id,
                SurveyQuestion.survey_id == ResponseAnswer.survey_id,
            ),
        )
        .join(
            ResponseAnswerOption,
            and_(
                ResponseAnswerOption.answer_id == ResponseAnswer.id,
                ResponseAnswerOption.question_id == ResponseAnswer.question_id,
            ),
        )
        .join(
            SurveyQuestionOption,
            and_(
                SurveyQuestionOption.question_id == ResponseAnswerOption.question_id,
                SurveyQuestionOption.id == ResponseAnswerOption.option_id,
            ),
        )
        .where(
            ResponseAnswer.survey_id == survey_id,
            SurveyQuestion.code == "Q39",
            SurveyQuestion.question_type == "NPS",
            SurveyQuestionOption.score_value.between(0, 10),
        )
        .group_by(SurveyQuestionOption.score_value)
        .order_by(SurveyQuestionOption.score_value)
    )
    return [(int(score), int(count)) for score, count in session.execute(statement).all() if score is not None]
