from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.survey import Survey, SurveyQuestion, SurveyQuestionOption, SurveySection


@dataclass(frozen=True)
class SurveyReadData:
    survey: Survey
    sections: list[SurveySection]
    questions: list[SurveyQuestion]
    options: list[SurveyQuestionOption]


def get_survey_by_code(survey_code: str) -> SurveyReadData | None:
    """Read one survey and its definition using a bounded number of queries."""
    with SessionLocal() as session:
        survey = session.scalar(select(Survey).where(Survey.code == survey_code))
        if survey is None:
            return None

        sections = list(
            session.scalars(
                select(SurveySection)
                .where(SurveySection.survey_id == survey.id)
                .order_by(SurveySection.position, SurveySection.id)
            ).all()
        )
        questions = list(
            session.scalars(
                select(SurveyQuestion)
                .where(
                    SurveyQuestion.survey_id == survey.id,
                    SurveyQuestion.question_number > 0,
                )
                .order_by(SurveyQuestion.section_id, SurveyQuestion.position, SurveyQuestion.id)
            ).all()
        )

        question_ids = [question.id for question in questions]
        options = (
            list(
                session.scalars(
                    select(SurveyQuestionOption)
                    .where(SurveyQuestionOption.question_id.in_(question_ids))
                    .order_by(SurveyQuestionOption.question_id, SurveyQuestionOption.position, SurveyQuestionOption.id)
                ).all()
            )
            if question_ids
            else []
        )

        return SurveyReadData(
            survey=survey,
            sections=sections,
            questions=questions,
            options=options,
        )
