import logging
from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories import management_repository
from app.services.organization_catalog import organization_catalog_service


logger = logging.getLogger(__name__)


class ManagementSurveyNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class _OrganizationResponseDistribution:
    total_responses: int
    regional_counts: Counter[str]
    base_counts: Counter[tuple[str, str]]
    unsafe_regionals: frozenset[str]
    unsafe_bases: frozenset[tuple[str, str]]
    total_is_safe: bool


def _hidden_counts_are_disclosure_safe(
    primary_counts: list[int], complementary_counts: list[int], minimum: int
) -> bool:
    """Return whether a published total leaves every primary hidden count ambiguous."""
    if not primary_counts:
        return True

    primary_count = len(primary_counts)
    residual = sum(primary_counts) + sum(complementary_counts)
    if complementary_counts:
        other_groups_minimum = (primary_count - 1) + len(complementary_counts) * minimum
        feasible_minimum = 1
        feasible_maximum = min(minimum - 1, residual - other_groups_minimum)
    else:
        other_groups_minimum = primary_count - 1
        other_groups_maximum = (primary_count - 1) * (minimum - 1)
        feasible_minimum = max(1, residual - other_groups_maximum)
        feasible_maximum = min(minimum - 1, residual - other_groups_minimum)

    return feasible_minimum < feasible_maximum


def _organization_response_distribution(
    session: Session, survey_id: int, minimum: int
) -> _OrganizationResponseDistribution:
    """Aggregate paired organizational segments and apply complementary suppression."""
    total_responses = management_repository.count_anonymous_responses(session, survey_id)
    catalog = organization_catalog_service.get_regional_sc_catalog()
    official_regionals = {regional.code for regional in catalog}
    owners_by_base: dict[str, set[str]] = {}
    for regional in catalog:
        for service_center in regional.service_centers:
            owners_by_base.setdefault(service_center.code, set()).add(regional.code)

    regional_counts: Counter[str] = Counter()
    base_counts: Counter[tuple[str, str]] = Counter()
    unsafe_regionals: set[str] = set()
    unsafe_bases: set[tuple[str, str]] = set()
    mapped_count = 0
    mappings_are_valid = True

    for regional_code, base_code, response_count in (
        management_repository.get_anonymous_response_counts_by_regional_and_base(
            session, survey_id
        )
    ):
        mapped_count += response_count
        regional_is_known = regional_code in official_regionals
        if regional_is_known:
            regional_counts[regional_code] += response_count
        else:
            mappings_are_valid = False

        owners = owners_by_base.get(base_code, set()) if base_code is not None else set()
        if len(owners) != 1:
            mappings_are_valid = False
            if regional_is_known:
                unsafe_regionals.add(regional_code)
            for owner in owners:
                unsafe_regionals.add(owner)
                unsafe_bases.add((owner, base_code))
            continue

        base_owner = next(iter(owners))
        if regional_code != base_owner:
            mappings_are_valid = False
            unsafe_regionals.add(base_owner)
            unsafe_bases.add((base_owner, base_code))
            if regional_is_known:
                unsafe_regionals.add(regional_code)
            continue

        base_counts[(base_owner, base_code)] += response_count

    for regional in catalog:
        regional_count = regional_counts.get(regional.code, 0)
        if 0 < regional_count < minimum:
            unsafe_regionals.add(regional.code)
        for service_center in regional.service_centers:
            key = (regional.code, service_center.code)
            base_count = base_counts.get(key, 0)
            if 0 < base_count < minimum:
                unsafe_bases.add(key)
                unsafe_regionals.add(regional.code)

    total_is_safe = (
        mapped_count == total_responses
        and mappings_are_valid
        and not 0 < total_responses < minimum
    )
    if total_is_safe:
        primary_counts = [
            base_counts[key]
            for key in unsafe_bases
            if key in base_counts and 0 < base_counts[key] < minimum
        ]
        total_is_safe = _hidden_counts_are_disclosure_safe(primary_counts, [], minimum)

        if not total_is_safe:
            candidates = sorted(
                (
                    (key, count)
                    for key, count in base_counts.items()
                    if key not in unsafe_bases and count >= minimum
                ),
                key=lambda item: (item[1], item[0]),
            )
            for key, count in candidates:
                if _hidden_counts_are_disclosure_safe(primary_counts, [count], minimum):
                    unsafe_bases.add(key)
                    unsafe_regionals.add(key[0])
                    total_is_safe = True
                    break

    return _OrganizationResponseDistribution(
        total_responses=total_responses,
        regional_counts=regional_counts,
        base_counts=base_counts,
        unsafe_regionals=frozenset(unsafe_regionals),
        unsafe_bases=frozenset(unsafe_bases),
        total_is_safe=total_is_safe,
    )


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
    distribution = _organization_response_distribution(
        session, survey.id, int(survey.min_group_size)
    )
    anonymous_response_count = distribution.total_responses
    total_is_safe = distribution.total_is_safe
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
        "completed_participations": (
            _privacy_safe_count(completed_participations, int(min_group_size))
            if total_is_safe
            else None
        ),
        "anonymous_response_count": anonymous_response_count if total_is_safe else None,
        "respondent_count": respondent_count if total_is_safe else None,
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
    distribution = _organization_response_distribution(
        session, survey.id, int(survey.min_group_size)
    )
    total_responses = distribution.total_responses
    total_is_safe = distribution.total_is_safe
    pillar_counts_are_consistent = all(count <= total_responses for count in respondent_counts.values())
    publish_respondent_counts = total_is_safe and pillar_counts_are_consistent

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
                "respondent_count": (
                    respondent_count
                    if publish_respondent_counts
                    and _privacy_safe_count(respondent_count, int(survey.min_group_size)) is not None
                    else None
                ),
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


def get_survey_adherence(session: Session, survey_code: str) -> dict[str, object]:
    """Return anonymous form counts by the approved Regional catalog."""
    logger.info("management adherence analytics requested")
    survey = management_repository.get_survey_by_code(session, survey_code)
    if survey is None:
        raise ManagementSurveyNotFoundError

    minimum = int(survey.min_group_size)
    distribution = _organization_response_distribution(session, survey.id, minimum)
    total_responses = distribution.total_responses
    counts_by_regional = distribution.regional_counts
    catalog = organization_catalog_service.get_regional_sc_catalog()
    regionals = []
    for regional in catalog:
        raw_regional_count = counts_by_regional.get(regional.code, 0)
        regional_is_safe = (
            regional.code not in distribution.unsafe_regionals
            and (raw_regional_count == 0 or raw_regional_count >= minimum)
        )
        regional_count = raw_regional_count if regional_is_safe else None
        bases = []
        for service_center in regional.service_centers:
            key = (regional.code, service_center.code)
            raw_base_count = distribution.base_counts.get(key, 0)
            base_is_safe = (
                key not in distribution.unsafe_bases
                and (raw_base_count == 0 or raw_base_count >= minimum)
            )
            bases.append(
                {
                    "base_code": service_center.code,
                    "base_name": service_center.display_name_override or service_center.name,
                    "response_count": raw_base_count if base_is_safe else None,
                    "analytics_available": base_is_safe and raw_base_count >= minimum,
                }
            )
        bases.sort(
            key=lambda item: (
                0 if item["analytics_available"] else 1 if item["response_count"] is None else 2,
                -int(item["response_count"] or 0) if item["analytics_available"] else 0,
                next(
                    index
                    for index, service_center in enumerate(regional.service_centers)
                    if service_center.code == item["base_code"]
                ),
            )
        )
        regionals.append(
            {
                "regional_code": regional.code,
                "regional_name": regional.display_name or regional.code,
                "response_count": regional_count,
                "analytics_available": (
                    regional_count is not None and raw_regional_count >= minimum
                ),
                "base_count": len(regional.service_centers),
                "bases": bases,
            }
        )

    regionals.sort(
        key=lambda item: (
            0 if item["analytics_available"] else 1 if item["response_count"] is None else 2,
            -int(item["response_count"] or 0) if item["analytics_available"] else 0,
            next(index for index, regional in enumerate(catalog) if regional.code == item["regional_code"]),
        )
    )
    total_bases = sum(len(regional.service_centers) for regional in catalog)
    result = {
        "survey_code": survey.code,
        "survey_status": survey.status,
        "min_group_size": minimum,
        "total_regionals": len(catalog),
        "total_bases": total_bases,
        "regionals_with_results": sum(
            regional["analytics_available"] for regional in regionals
        ),
        "total_responses": total_responses if distribution.total_is_safe else None,
        "regionals": regionals,
    }
    logger.info("management adherence analytics generated")
    return result


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
    organization_distribution = _organization_response_distribution(
        session, survey.id, minimum
    )
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

    def group_analysis(
        segment_type: str,
        segment_code: str,
        *,
        suppress_counts: bool = False,
    ) -> tuple[dict[str, object], int]:
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
                    "respondent_count": (
                        None
                        if suppress_counts
                        else _privacy_safe_count(raw_question_respondents, minimum)
                    ),
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
                "respondent_count": (
                    None
                    if suppress_counts
                    else _privacy_safe_count(raw_group_respondents, minimum)
                ),
                "questions": [row[0] for row in question_rows],
            },
            raw_group_respondents,
        )

    regional_rows: list[tuple[dict[str, object], int, int]] = []
    for regional_position, regional in enumerate(organization_catalog_service.get_regional_sc_catalog()):
        regional_analysis, regional_raw_count = group_analysis(
            "REGIONAL",
            regional.code,
            suppress_counts=regional.code in organization_distribution.unsafe_regionals,
        )
        sc_rows: list[tuple[dict[str, object], int, int]] = []
        for sc_position, service_center in enumerate(regional.service_centers):
            sc_analysis, sc_raw_count = group_analysis(
                "BASE",
                service_center.code,
                suppress_counts=(regional.code, service_center.code)
                in organization_distribution.unsafe_bases,
            )
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
