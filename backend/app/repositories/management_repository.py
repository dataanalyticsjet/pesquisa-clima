from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from app.models.anonymous_responses import (
    AnonymousResponse,
    AnonymousResponseSegment,
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
            SurveyQuestion.question_number > 0,
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
            SurveyQuestion.question_number > 0,
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
            SurveyQuestion.question_number > 0,
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
            SurveyQuestion.question_number > 0,
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


def get_attention_question_definitions(
    session: Session, survey_id: int
) -> list[tuple[int, str, str, int]]:
    """Return all database-defined SCORE/LIKERT questions in display order."""
    statement = (
        select(
            SurveyQuestion.id,
            SurveyQuestion.code,
            SurveyQuestion.text,
            SurveyQuestion.position,
        )
        .where(
            SurveyQuestion.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
        )
        .order_by(SurveyQuestion.position)
    )
    return [
        (int(question_id), str(code), str(text), int(position))
        for question_id, code, text, position in session.execute(statement).all()
    ]


def get_attention_group_respondent_counts(
    session: Session, survey_id: int
) -> list[tuple[str, str, int]]:
    """Count distinct anonymous respondents with valid Likert answers per group."""
    statement = (
        select(
            AnonymousResponseSegment.segment_type,
            AnonymousResponseSegment.segment_code,
            func.count(distinct(ResponseAnswer.response_id)),
        )
        .select_from(ResponseAnswer)
        .join(
            AnonymousResponse,
            and_(
                AnonymousResponse.response_id == ResponseAnswer.response_id,
                AnonymousResponse.survey_id == ResponseAnswer.survey_id,
            ),
        )
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
        .join(
            AnonymousResponseSegment,
            AnonymousResponseSegment.response_id == ResponseAnswer.response_id,
        )
        .where(
            ResponseAnswer.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
            SurveyQuestionOption.score_value.between(1, 5),
            AnonymousResponseSegment.segment_type.in_(("REGIONAL", "BASE")),
        )
        .group_by(
            AnonymousResponseSegment.segment_type,
            AnonymousResponseSegment.segment_code,
        )
    )
    return [
        (str(segment_type), str(segment_code), int(respondent_count))
        for segment_type, segment_code, respondent_count in session.execute(statement).all()
    ]


def get_attention_score_counts(
    session: Session, survey_id: int
) -> list[tuple[str, str, int, str, str, int, int | None, int]]:
    """Aggregate answer rows by anonymous group, eligible question, and stored score."""
    statement = (
        select(
            AnonymousResponseSegment.segment_type,
            AnonymousResponseSegment.segment_code,
            SurveyQuestion.id,
            SurveyQuestion.code,
            SurveyQuestion.text,
            SurveyQuestion.position,
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
        .join(
            AnonymousResponseSegment,
            AnonymousResponseSegment.response_id == ResponseAnswer.response_id,
        )
        .where(
            ResponseAnswer.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
            AnonymousResponseSegment.segment_type.in_(("REGIONAL", "BASE")),
        )
        .group_by(
            AnonymousResponseSegment.segment_type,
            AnonymousResponseSegment.segment_code,
            SurveyQuestion.id,
            SurveyQuestion.code,
            SurveyQuestion.text,
            SurveyQuestion.position,
            SurveyQuestionOption.score_value,
        )
    )
    rows = session.execute(statement).all()
    return [
        (
            str(segment_type),
            str(segment_code),
            int(question_id),
            str(question_code),
            str(question_text),
            int(position),
            int(score_value) if score_value is not None else None,
            int(answer_count),
        )
        for segment_type, segment_code, question_id, question_code, question_text, position, score_value, answer_count in rows
    ]


def get_attention_question_respondent_counts(
    session: Session, survey_id: int
) -> list[tuple[str, str, int, int]]:
    """Count distinct anonymous respondents with valid scores per group/question."""
    statement = (
        select(
            AnonymousResponseSegment.segment_type,
            AnonymousResponseSegment.segment_code,
            SurveyQuestion.id,
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
        .join(
            AnonymousResponseSegment,
            AnonymousResponseSegment.response_id == ResponseAnswer.response_id,
        )
        .where(
            ResponseAnswer.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.analysis_role == "SCORE",
            SurveyQuestion.question_type == "LIKERT",
            SurveyQuestionOption.score_value.between(1, 5),
            AnonymousResponseSegment.segment_type.in_(("REGIONAL", "BASE")),
        )
        .group_by(
            AnonymousResponseSegment.segment_type,
            AnonymousResponseSegment.segment_code,
            SurveyQuestion.id,
        )
    )
    return [
        (str(segment_type), str(segment_code), int(question_id), int(respondent_count))
        for segment_type, segment_code, question_id, respondent_count in session.execute(statement).all()
    ]


def get_voice_question_definitions(
    session: Session, survey_id: int
) -> list[tuple[str, str, str]]:
    """Load the official text and type for the three open-text voice questions."""
    statement = (
        select(SurveyQuestion.code, SurveyQuestion.text, SurveyQuestion.question_type)
        .where(
            SurveyQuestion.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.code.in_(("Q40", "Q41", "Q42")),
        )
        .order_by(SurveyQuestion.position)
    )
    return [
        (str(code), str(question_text), str(question_type))
        for code, question_text, question_type in session.execute(statement).all()
    ]


def get_voice_respondent_counts(session: Session, survey_id: int) -> list[tuple[str, int]]:
    """Count distinct anonymous responses with nonblank text for each voice question."""
    statement = (
        select(
            SurveyQuestion.code,
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
        .where(
            ResponseAnswer.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.code.in_(("Q40", "Q41", "Q42")),
            ResponseAnswer.text_value.is_not(None),
            func.trim(ResponseAnswer.text_value) != "",
        )
        .group_by(SurveyQuestion.code)
    )
    return [
        (str(code), int(respondent_count))
        for code, respondent_count in session.execute(statement).all()
    ]


def get_voice_text_answers(session: Session, survey_id: int) -> list[tuple[str, str]]:
    """Retrieve only the question code and anonymous text, with no technical identifiers."""
    statement = (
        select(SurveyQuestion.code, ResponseAnswer.text_value)
        .select_from(ResponseAnswer)
        .join(
            SurveyQuestion,
            and_(
                SurveyQuestion.id == ResponseAnswer.question_id,
                SurveyQuestion.survey_id == ResponseAnswer.survey_id,
            ),
        )
        .where(
            ResponseAnswer.survey_id == survey_id,
            SurveyQuestion.question_number > 0,
            SurveyQuestion.code.in_(("Q40", "Q41", "Q42")),
            ResponseAnswer.text_value.is_not(None),
            func.trim(ResponseAnswer.text_value) != "",
        )
    )
    return [
        (str(code), str(text_value))
        for code, text_value in session.execute(statement).all()
        if text_value is not None
    ]
