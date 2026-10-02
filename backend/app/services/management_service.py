import logging

from sqlalchemy.orm import Session

from app.repositories import management_repository


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
