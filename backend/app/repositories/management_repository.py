from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from app.models.anonymous_responses import (
    AnonymousResponse,
    ResponseAnswer,
    ResponseAnswerOption,
)
from app.models.participation import SurveyParticipation
from app.models.survey import Survey, SurveyQuestion, SurveyQuestionOption, SurveySection


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


def get_pillar_definitions(session: Session, survey_id: int) -> list[tuple[str, str, int, int]]:
    """Load analytical sections and eligible SCORE/LIKERT question counts."""
    statement = (
        select(
            SurveySection.code,
            SurveySection.title,
            SurveySection.position,
            func.count(SurveyQuestion.id),
        )
        .select_from(SurveySection)
        .join(
            SurveyQuestion,
            and_(
                SurveyQuestion.section_id == SurveySection.id,
                SurveyQuestion.survey_id == SurveySection.survey_id,
            ),
        )
        .where(
            SurveySection.survey_id == survey_id,
            SurveySection.analysis_type.in_(("SCORE", "MIXED")),
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
        )
        .group_by(SurveySection.id, SurveySection.code, SurveySection.title, SurveySection.position)
        .order_by(SurveySection.position)
    )
    return [
        (str(code), str(title), int(position), int(question_count))
        for code, title, position, question_count in session.execute(statement).all()
    ]


def get_pillar_answer_score_counts(
    session: Session, survey_id: int
) -> list[tuple[str, int | None, int]]:
    """Aggregate anonymous answer rows by section and stored option score."""
    statement = (
        select(
            SurveySection.code,
            SurveyQuestionOption.score_value,
            func.count(distinct(ResponseAnswer.id)),
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
            SurveySection,
            and_(
                SurveySection.id == SurveyQuestion.section_id,
                SurveySection.survey_id == SurveyQuestion.survey_id,
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
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
        )
        .group_by(SurveySection.code, SurveyQuestionOption.score_value)
        .order_by(SurveySection.code, SurveyQuestionOption.score_value)
    )
    return [
        (str(section_code), int(score) if score is not None else None, int(answer_count))
        for section_code, score, answer_count in session.execute(statement).all()
    ]


def get_pillar_respondent_counts(session: Session, survey_id: int) -> list[tuple[str, int]]:
    """Count distinct anonymous responses with a valid answer in each section."""
    statement = (
        select(
            SurveySection.code,
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
            SurveySection,
            and_(
                SurveySection.id == SurveyQuestion.section_id,
                SurveySection.survey_id == SurveyQuestion.survey_id,
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
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
            SurveyQuestionOption.score_value.between(1, 5),
        )
        .group_by(SurveySection.code)
        .order_by(SurveySection.code)
    )
    return [
        (str(section_code), int(respondent_count))
        for section_code, respondent_count in session.execute(statement).all()
    ]
