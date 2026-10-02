import logging
from collections import Counter

from sqlalchemy.orm import Session

from app.repositories import management_repository
from app.services.organization_catalog import organization_catalog_service


logger = logging.getLogger(__name__)


class ManagementSurveyNotFoundError(Exception):
    pass


def _calculate_nps(score_counts: list[tuple[int, int]]) -> tuple[float | None, int]:
    detractors = sum(count for score, count in score_counts if 0 <= score <= 6)
    promoters = sum(count for score, count in score_counts if 9 <= score <= 10)
    nps_responses = sum(count for _, count in score_counts)
    if nps_responses == 0:
        return None, 0
    return round((promoters - detractors) * 100 / nps_responses, 2), nps_responses


def get_survey_overview(session: Session, survey_code: str) -> dict[str, object] | None:
    logger.info("management overview requested")
    survey = management_repository.get_survey_by_code(session, survey_code)
    if survey is None:
        logger.info("management overview survey not found")
        raise ManagementSurveyNotFoundError

    completed_participations = management_repository.count_completed_participations(session, survey.id)
    anonymous_response_count = management_repository.count_anonymous_responses(session, survey.id)
    respondent_count = anonymous_response_count
    min_group_size = survey.min_group_size
    analytics_available = respondent_count >= min_group_size

    nps = None
    if analytics_available:
        score_counts = management_repository.get_q39_score_counts(session, survey.id)
        candidate_nps, nps_responses = _calculate_nps(score_counts)
        if nps_responses >= min_group_size:
            nps = candidate_nps
    else:
        logger.info("management analytics suppressed")

    result: dict[str, object] = {
        "survey_code": survey.code,
        "survey_status": survey.status,
        "min_group_size": min_group_size,
        "completed_participations": completed_participations,
        "anonymous_response_count": anonymous_response_count,
        "respondent_count": respondent_count,
        "analytics_available": analytics_available,
        "nps": nps,
        "invited_count": None,
        "adherence_percent": None,
        "invited_population_source_configured": False,
    }
    logger.info("management overview generated")
    return result


def _calculate_pillar_index(score_counts: list[tuple[int | None, int]]) -> float | None:
    valid_answers = [
        (score, count)
        for score, count in score_counts
        if score is not None and 1 <= score <= 5 and count > 0
    ]
    answer_count = sum(count for _, count in valid_answers)
    if answer_count == 0:
        return None

    scaled_total = sum(((score - 1) / 4) * 100 * count for score, count in valid_answers)
    return round(scaled_total / answer_count, 2)


def get_survey_pillars(session: Session, survey_code: str) -> dict[str, object]:
    logger.info("management pillars requested")
    survey = management_repository.get_survey_by_code(session, survey_code)
    if survey is None:
        logger.info("management overview survey not found")
        raise ManagementSurveyNotFoundError

    definitions = management_repository.get_pillar_definitions(session, survey.id)
    answer_score_counts = management_repository.get_pillar_answer_score_counts(session, survey.id)
    respondent_counts = dict(management_repository.get_pillar_respondent_counts(session, survey.id))

    scores_by_section: dict[str, list[tuple[int | None, int]]] = {}
    invalid_score_found = False
    for section_code, score, answer_count in answer_score_counts:
        if score is None or not 1 <= score <= 5:
            invalid_score_found = True
            continue
        scores_by_section.setdefault(section_code, []).append((score, answer_count))

    if invalid_score_found:
        logger.warning("management pillar invalid option scores ignored")

    pillars: list[dict[str, object]] = []
    for section_code, title, _position, question_count in definitions:
        respondent_count = respondent_counts.get(section_code, 0)
        analytics_available = respondent_count >= survey.min_group_size
        pillar_index = None
        if analytics_available:
            pillar_index = _calculate_pillar_index(scores_by_section.get(section_code, []))
        else:
            logger.info("management pillar analytics suppressed")

        pillars.append(
            {
                "code": section_code,
                "title": title,
                "question_count": question_count,
                "respondent_count": respondent_count,
                "analytics_available": analytics_available,
                "index": pillar_index,
            }
        )

    logger.info("management pillars generated")
    return {
        "survey_code": survey.code,
        "survey_status": survey.status,
        "min_group_size": survey.min_group_size,
        "pillars": pillars,
    }


def _privacy_safe_count(count: int, minimum: int) -> int | None:
    if count == 0:
        return 0
    if count < minimum:
        return None
    return count


def _attention_rate(attention_answers: int, valid_answers: int) -> float | None:
    if valid_answers == 0:
        return None
    return round(attention_answers * 100 / valid_answers, 2)


def get_survey_attention(session: Session, survey_code: str) -> dict[str, object]:
    """Build the privacy-suppressed attention view from anonymous aggregates."""
    logger.info("management attention analytics requested")
    survey = management_repository.get_survey_by_code(session, survey_code)
    if survey is None:
        logger.info("management attention survey not found")
        raise ManagementSurveyNotFoundError

    minimum = int(survey.min_group_size)
    questions = management_repository.get_attention_question_definitions(session, survey.id)
    group_respondent_counts = {
        (segment_type, segment_code): count
        for segment_type, segment_code, count in management_repository.get_attention_group_respondent_counts(
            session, survey.id
        )
    }

    answer_counts: dict[tuple[str, str, int], dict[int, int]] = {}
    invalid_score_found = False
    for segment_type, segment_code, question_id, _question_code, _question_text, _position, score, answer_count in (
        management_repository.get_attention_score_counts(session, survey.id)
    ):
        if score is None or not 1 <= score <= 5:
            invalid_score_found = True
            continue
        counts = answer_counts.setdefault((segment_type, segment_code, question_id), {})
        counts[score] = counts.get(score, 0) + answer_count
    if invalid_score_found:
        logger.warning("management attention invalid score ignored")

    question_respondent_counts = {
        (segment_type, segment_code, question_id): count
        for segment_type, segment_code, question_id, count in management_repository.get_attention_question_respondent_counts(
            session, survey.id
        )
    }

    question_definitions = [
        {"id": question_id, "code": code, "text": text, "position": position}
        for question_id, code, text, position in questions
    ]

    def group_analysis(segment_type: str, segment_code: str) -> tuple[dict[str, object], int]:
        raw_group_respondents = group_respondent_counts.get((segment_type, segment_code), 0)
        valid_answer_total = 0
        attention_answer_total = 0
        question_rows: list[tuple[dict[str, object], int, int]] = []

        for question in question_definitions:
            question_id = int(question["id"])
            scores = answer_counts.get((segment_type, segment_code, question_id), {})
            valid_answers = sum(scores.values())
            attention_answers = scores.get(1, 0) + scores.get(2, 0)
            raw_question_respondents = question_respondent_counts.get(
                (segment_type, segment_code, question_id), 0
            )
            question_available = raw_question_respondents >= minimum and valid_answers > 0
            question_rate = (
                _attention_rate(attention_answers, valid_answers) if question_available else None
            )
            question_rows.append((
                {
                    "question_code": question["code"],
                    "question_text": question["text"],
                    "analytics_available": question_available,
                    "attention_rate": question_rate,
                    "respondent_count": _privacy_safe_count(raw_question_respondents, minimum),
                },
                int(question["position"]),
                raw_question_respondents,
            ))
            valid_answer_total += valid_answers
            attention_answer_total += attention_answers

        question_rows.sort(key=lambda row: (
            0 if row[0]["analytics_available"] else (2 if row[2] == 0 else 1),
            -float(row[0]["attention_rate"] or 0) if row[0]["analytics_available"] else 0,
            row[1],
        ))

        group_available = raw_group_respondents >= minimum and valid_answer_total > 0
        group_rate = (
            _attention_rate(attention_answer_total, valid_answer_total) if group_available else None
        )
        if not group_available:
            logger.info("management attention group suppressed")
        return (
            {
                "attention_rate": group_rate,
                "analytics_available": group_available,
                "respondent_count": _privacy_safe_count(raw_group_respondents, minimum),
                "questions": [row[0] for row in question_rows],
            },
            raw_group_respondents,
        )

    regional_rows: list[tuple[dict[str, object], int, int]] = []
    for regional_position, regional in enumerate(organization_catalog_service.get_regional_sc_catalog()):
        regional_analysis, regional_raw_count = group_analysis("REGIONAL", regional.code)
        sc_rows: list[tuple[dict[str, object], int, int]] = []
        for sc_position, service_center in enumerate(regional.service_centers):
            sc_analysis, sc_raw_count = group_analysis("BASE", service_center.code)
            sc_rows.append((
                {
                    "sc_code": service_center.code,
                    "sc_name": service_center.name,
                    "display_name": service_center.display_name,
                    **sc_analysis,
                },
                sc_raw_count,
                sc_position,
            ))
        sc_rows.sort(key=lambda row: (
            0 if row[0]["analytics_available"] else (2 if row[1] == 0 else 1),
            -float(row[0]["attention_rate"] or 0) if row[0]["analytics_available"] else 0,
            row[2],
        ))
        regional_rows.append((
            {
                "regional_code": regional.code,
                **regional_analysis,
                "scs": [row[0] for row in sc_rows],
            },
            regional_raw_count,
            regional_position,
        ))

    regional_rows.sort(key=lambda row: (
        0 if row[0]["analytics_available"] else (2 if row[1] == 0 else 1),
        -float(row[0]["attention_rate"] or 0) if row[0]["analytics_available"] else 0,
        row[2],
    ))
    logger.info("management attention analytics generated")
    return {
        "survey_code": survey.code,
        "survey_status": survey.status,
        "min_group_size": minimum,
        "regionals": [row[0] for row in regional_rows],
    }


def _voice_visible_count(count: int, minimum: int) -> int | None:
    if count == 0:
        return 0
    if count < minimum:
        return None
    return count


def _normalize_voice_term(text: str) -> str:
    return " ".join(text.split()).casefold()


def get_survey_voice(session: Session, survey_code: str) -> dict[str, object]:
    """Return privacy-thresholded anonymous comments and Q42 term aggregates."""
    logger.info("voice analytics requested")
    survey = management_repository.get_survey_by_code(session, survey_code)
    if survey is None:
        raise ManagementSurveyNotFoundError

    definitions = management_repository.get_voice_question_definitions(session, survey.id)
    respondent_counts = dict(
        management_repository.get_voice_respondent_counts(session, survey.id)
    )
    text_by_question: dict[str, list[str]] = {}
    for question_code, text in management_repository.get_voice_text_answers(session, survey.id):
        if text.strip():
            text_by_question.setdefault(question_code, []).append(text)

    definitions_by_code = {
        code: {"question_text": question_text, "question_type": question_type}
        for code, question_text, question_type in definitions
    }
    minimum = int(survey.min_group_size)
    questions: list[dict[str, object]] = []
    suppressed = False

    for question_code in ("Q40", "Q41", "Q42"):
        definition = definitions_by_code.get(question_code)
        if definition is None:
            continue

        respondent_count = respondent_counts.get(question_code, 0)
        analytics_available = respondent_count > 0 and respondent_count >= minimum
        if not analytics_available:
            suppressed = True

        common: dict[str, object] = {
            "question_code": question_code,
            "question_text": definition["question_text"],
            "question_type": definition["question_type"],
            "analytics_available": analytics_available,
            "respondent_count": _voice_visible_count(respondent_count, minimum),
        }

        if question_code == "Q42":
            normalized_terms = (
                (_normalize_voice_term(text) for text in text_by_question.get(question_code, []))
                if analytics_available
                else ()
            )
            terms = Counter(term for term in normalized_terms if term)
            common["terms"] = [
                {"term": term, "count": count}
                for term, count in sorted(terms.items(), key=lambda item: (-item[1], item[0]))
            ]
            questions.append(common)
            continue

        comments = text_by_question.get(question_code, []) if analytics_available else []
        common["comments"] = sorted(
            comments,
            key=lambda text: (_normalize_voice_term(text), text.casefold(), text),
        )
        questions.append(common)

    if suppressed:
        logger.info("voice analytics suppressed")
    logger.info("voice analytics generated")
    return {
        "survey_code": survey.code,
        "survey_status": survey.status,
        "min_group_size": minimum,
        "questions": questions,
    }
