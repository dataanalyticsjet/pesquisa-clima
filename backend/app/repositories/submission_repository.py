from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anonymous_responses import (
    AnonymousResponse,
    AnonymousResponseSegment,
    ResponseAnswer,
    ResponseAnswerOption,
)
from app.models.participation import SurveyParticipation
from app.models.survey import Survey, SurveyQuestion, SurveyQuestionOption


def get_survey_by_code(session: Session, survey_code: str) -> Survey | None:
    return session.scalar(select(Survey).where(Survey.code == survey_code))


def get_participation(
    session: Session, survey_id: int, user_id: int
) -> SurveyParticipation | None:
    return session.scalar(
        select(SurveyParticipation).where(
            SurveyParticipation.survey_id == survey_id,
            SurveyParticipation.user_id == user_id,
        )
    )


def get_questions_by_survey(session: Session, survey_id: int) -> list[SurveyQuestion]:
    statement = (
        select(SurveyQuestion)
        .where(SurveyQuestion.survey_id == survey_id)
        .order_by(SurveyQuestion.question_number, SurveyQuestion.id)
    )
    return list(session.scalars(statement).all())


def get_options_by_question_ids(
    session: Session, question_ids: list[int]
) -> list[SurveyQuestionOption]:
    if not question_ids:
        return []
    statement = (
        select(SurveyQuestionOption)
        .where(SurveyQuestionOption.question_id.in_(question_ids))
        .order_by(SurveyQuestionOption.question_id, SurveyQuestionOption.position)
    )
    return list(session.scalars(statement).all())


def add_anonymous_response(session: Session, response: AnonymousResponse) -> None:
    session.add(response)
    session.flush()


def add_response_answer(session: Session, answer: ResponseAnswer) -> None:
    session.add(answer)
    session.flush()


def add_response_answer_option(session: Session, option: ResponseAnswerOption) -> None:
    session.add(option)


def add_anonymous_response_segment(
    session: Session, segment: AnonymousResponseSegment
) -> None:
    session.add(segment)


def add_survey_participation(
    session: Session, participation: SurveyParticipation
) -> None:
    session.add(participation)
    session.flush()
