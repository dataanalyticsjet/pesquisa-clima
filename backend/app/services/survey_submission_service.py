import logging
import re
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.anonymous_responses import (
    AnonymousResponse,
    AnonymousResponseSegment,
    ResponseAnswer,
    ResponseAnswerOption,
)
from app.models.participation import SurveyParticipation
from app.models.survey import SurveyQuestion, SurveyQuestionOption
from app.repositories import submission_repository
from app.schemas.responses import SurveyAnswerSubmission, SurveySubmissionRequest
from app.services.cnpj import normalize_cnpj, validate_cnpj
from app.services.organization_catalog import organization_catalog_service


logger = logging.getLogger(__name__)
CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_TEXT_BYTES = 60_000
OPTION_TYPES = {"SELECT", "SINGLE_CHOICE", "MULTIPLE_CHOICE", "LIKERT", "NPS"}
TEXT_TYPES = {"TEXTAREA", "SHORT_TEXT"}
ORG_SEGMENT_TYPES = {
    "ORG_REGIONAL": "REGIONAL",
    "ORG_BASE": "BASE",
    "ORG_CNPJ": "CNPJ",
}


class SurveySubmissionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ValidatedAnswer:
    question: SurveyQuestion
    text_value: str | None
    option_ids: tuple[int, ...] = ()
    organization_code: str | None = None


def _is_participation_duplicate(error: IntegrityError) -> bool:
    original = error.orig
    message = str(original).lower()
    if "uq_survey_participation_survey_user" in message:
        return True
    return (
        "unique constraint failed" in message
        and "survey_participation.survey_id" in message
        and "survey_participation.user_id" in message
    )


def _normalize_answers(
    request: SurveySubmissionRequest,
    questions: list[SurveyQuestion],
    options: list[SurveyQuestionOption],
    organization_catalog,
) -> tuple[list[ValidatedAnswer], dict[str, str]]:
    questions_by_code = {question.code: question for question in questions}
    question_options: dict[int, dict[str, SurveyQuestionOption]] = {}
    for option in options:
        question_options.setdefault(option.question_id, {})[option.code] = option

    submitted_by_code: dict[str, SurveyAnswerSubmission] = {}
    for submitted in request.answers:
        if not CODE_PATTERN.fullmatch(submitted.question_code):
            raise SurveySubmissionError("INVALID_ANSWER")
        if submitted.question_code in submitted_by_code:
            raise SurveySubmissionError("INVALID_ANSWER")
        if submitted.question_code not in questions_by_code:
            raise SurveySubmissionError("INVALID_ANSWER")
        if (submitted.option_codes is None) == (submitted.text_value is None):
            raise SurveySubmissionError("INVALID_ANSWER")
        if submitted.option_codes is not None and any(
            not CODE_PATTERN.fullmatch(code) for code in submitted.option_codes
        ):
            raise SurveySubmissionError("INVALID_ANSWER")
        if submitted.text_value is not None and len(
            submitted.text_value.encode("utf-8")
        ) > MAX_TEXT_BYTES:
            raise SurveySubmissionError("INVALID_ANSWER")
        submitted_by_code[submitted.question_code] = submitted

    for question in questions:
        answer = submitted_by_code.get(question.code)
        if answer is None:
            if question.required:
                raise SurveySubmissionError("MISSING_REQUIRED_ANSWER")
            continue
        is_cnpj_question = question.option_source == "ORG_CNPJ"
        if question.question_type in OPTION_TYPES and not is_cnpj_question and (
            answer.option_codes is None or answer.text_value is not None
        ):
            raise SurveySubmissionError("INVALID_ANSWER")
        if is_cnpj_question and question.question_type != "SELECT":
            raise SurveySubmissionError("INVALID_ANSWER")
        if question.question_type in TEXT_TYPES and (
            answer.text_value is None or answer.option_codes is not None
        ):
            raise SurveySubmissionError("INVALID_ANSWER")
        if question.required:
            if is_cnpj_question:
                has_unknown_selection = answer.option_codes == ["unknown"]
                has_cnpj_text = answer.text_value is not None and bool(answer.text_value.strip())
                if not has_unknown_selection and not has_cnpj_text:
                    raise SurveySubmissionError("MISSING_REQUIRED_ANSWER")
            elif question.question_type in OPTION_TYPES and not answer.option_codes:
                raise SurveySubmissionError("MISSING_REQUIRED_ANSWER")
            if question.question_type in TEXT_TYPES and not answer.text_value.strip():
                raise SurveySubmissionError("MISSING_REQUIRED_ANSWER")

    normalized: list[ValidatedAnswer] = []
    organization_codes: dict[str, str] = {}
    for question in questions:
        answer = submitted_by_code.get(question.code)
        if answer is None:
            continue
        if question.question_type not in OPTION_TYPES | TEXT_TYPES:
            raise SurveySubmissionError("INVALID_ANSWER")

        if question.option_source == "ORG_CNPJ":
            if question.question_type != "SELECT":
                raise SurveySubmissionError("INVALID_ANSWER")
            if answer.text_value is not None:
                if answer.option_codes is not None or not validate_cnpj(answer.text_value):
                    raise SurveySubmissionError("INVALID_ANSWER")
                normalized_value = normalize_cnpj(answer.text_value)
                organization_codes[question.option_source] = normalized_value
                normalized.append(
                    ValidatedAnswer(
                        question=question,
                        text_value=normalized_value,
                        organization_code=normalized_value,
                    )
                )
                continue

            if answer.option_codes != ["unknown"]:
                raise SurveySubmissionError("INVALID_ANSWER")
            sentinel = question_options.get(question.id, {}).get("unknown")
            if sentinel is None or sentinel.label != "Não sei informar":
                raise SurveySubmissionError("INVALID_OPTION")
            organization_codes[question.option_source] = "unknown"
            normalized.append(
                ValidatedAnswer(
                    question=question,
                    text_value=None,
                    option_ids=(sentinel.id,),
                    organization_code="unknown",
                )
            )
            continue

        if question.question_type in TEXT_TYPES:
            if answer.option_codes is not None or answer.text_value is None:
                raise SurveySubmissionError("INVALID_ANSWER")
            normalized.append(
                ValidatedAnswer(question=question, text_value=answer.text_value)
            )
            continue

        if answer.text_value is not None or answer.option_codes is None:
            raise SurveySubmissionError("INVALID_ANSWER")
        codes = answer.option_codes
        if question.question_type == "MULTIPLE_CHOICE":
            if not codes:
                raise SurveySubmissionError("INVALID_MULTIPLE_CHOICE")
            if len(codes) != len(set(codes)):
                raise SurveySubmissionError("INVALID_MULTIPLE_CHOICE")
        elif len(codes) != 1:
            raise SurveySubmissionError("INVALID_ANSWER")

        if question.option_source in ORG_SEGMENT_TYPES:
            if question.question_type != "SELECT":
                raise SurveySubmissionError("INVALID_ANSWER")
            option_code = codes[0]
            regional_code = organization_codes.get("ORG_REGIONAL")
            base_code = organization_codes.get("ORG_BASE")
            valid = organization_catalog.validate_selection(
                question.option_source,
                option_code,
                regional_code=regional_code,
                base_code=base_code,
            )
            if valid is None:
                raise SurveySubmissionError("ORGANIZATION_CATALOG_UNAVAILABLE")
            if not valid:
                raise SurveySubmissionError("INVALID_OPTION")
            organization_codes[question.option_source] = option_code
            normalized.append(
                ValidatedAnswer(
                    question=question,
                    text_value=option_code,
                    organization_code=option_code,
                )
            )
            continue

        options_by_code = question_options.get(question.id, {})
        selected = [options_by_code.get(code) for code in codes]
        if any(option is None for option in selected):
            raise SurveySubmissionError("INVALID_OPTION")
        if any(option.is_exclusive for option in selected) and len(selected) != 1:
            raise SurveySubmissionError("EXCLUSIVE_OPTION_CONFLICT")
        normalized.append(
            ValidatedAnswer(
                question=question,
                text_value=None,
                option_ids=tuple(option.id for option in selected),
            )
        )

    return normalized, organization_codes


def submit_survey(
    session: Session,
    survey_code: str,
    user_id: int,
    request: SurveySubmissionRequest,
    *,
    organization_catalog=None,
    response_id_factory: Callable[[], uuid.UUID] = uuid.uuid4,
) -> dict[str, bool]:
    catalog = organization_catalog or organization_catalog_service
    try:
        # get_current_user may already have opened this request's SQLAlchemy transaction.
        if not session.in_transaction():
            session.begin()

        survey = submission_repository.get_survey_by_code(session, survey_code)
        if survey is None:
            raise SurveySubmissionError("SURVEY_NOT_FOUND")
        if survey.status != "ACTIVE":
            raise SurveySubmissionError("SURVEY_NOT_ACTIVE")

        if submission_repository.get_participation(session, survey.id, user_id) is not None:
            raise SurveySubmissionError("SURVEY_ALREADY_COMPLETED")

        questions = submission_repository.get_questions_by_survey(session, survey.id)
        options = submission_repository.get_options_by_question_ids(
            session, [question.id for question in questions]
        )
        normalized, organization_codes = _normalize_answers(
            request, questions, options, catalog
        )

        response_id = str(response_id_factory())
        submission_repository.add_anonymous_response(
            session,
            AnonymousResponse(response_id=response_id, survey_id=survey.id),
        )

        for answer in normalized:
            answer_row = ResponseAnswer(
                response_id=response_id,
                survey_id=survey.id,
                question_id=answer.question.id,
                text_value=answer.text_value,
            )
            submission_repository.add_response_answer(session, answer_row)
            for option_id in answer.option_ids:
                submission_repository.add_response_answer_option(
                    session,
                    ResponseAnswerOption(
                        answer_id=answer_row.id,
                        question_id=answer.question.id,
                        option_id=option_id,
                    ),
                )

        for option_source, segment_type in ORG_SEGMENT_TYPES.items():
            segment_code = organization_codes.get(option_source)
            if not segment_code or (option_source == "ORG_CNPJ" and segment_code == "unknown"):
                continue
            submission_repository.add_anonymous_response_segment(
                session,
                AnonymousResponseSegment(
                    response_id=response_id,
                    segment_type=segment_type,
                    segment_code=segment_code,
                ),
            )

        submission_repository.add_survey_participation(
            session,
            SurveyParticipation(
                survey_id=survey.id,
                user_id=user_id,
                status="COMPLETED",
                completed_on=date.today(),
            ),
        )
        session.commit()
    except SurveySubmissionError as error:
        session.rollback()
        if error.code == "ORGANIZATION_CATALOG_UNAVAILABLE":
            logger.warning("survey submission organization catalog unavailable")
        elif error.code == "SURVEY_ALREADY_COMPLETED":
            logger.info("survey submission duplicate participation")
        else:
            logger.info("survey submission validation failed")
        raise
    except IntegrityError as error:
        session.rollback()
        if _is_participation_duplicate(error):
            logger.info("survey submission duplicate participation")
            raise SurveySubmissionError("SURVEY_ALREADY_COMPLETED") from None
        logger.error("survey submission transaction failed")
        raise SurveySubmissionError("SUBMISSION_UNAVAILABLE") from None
    except Exception:
        session.rollback()
        logger.error("survey submission transaction failed")
        raise SurveySubmissionError("SUBMISSION_UNAVAILABLE") from None

    logger.info("survey submission completed")
    return {"submitted": True}
