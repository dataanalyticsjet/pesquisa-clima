from app.repositories.survey_repository import SurveyReadData, get_survey_by_code


class SurveyNotActiveError(Exception):
    pass


def get_survey_definition(survey_code: str, *, require_active: bool = False) -> dict[str, object] | None:
    data = get_survey_by_code(survey_code)
    if data is None:
        return None

    if require_active and data.survey.status != "ACTIVE":
        raise SurveyNotActiveError

    options_by_question: dict[int, list[object]] = {}
    for option in data.options:
        options_by_question.setdefault(option.question_id, []).append(option)

    questions_by_section: dict[int, list[object]] = {}
    for question in data.questions:
        questions_by_section.setdefault(question.section_id, []).append(question)

    sections = []
    for section in sorted(data.sections, key=lambda item: (item.position, item.id)):
        questions = []
        for question in sorted(questions_by_section.get(section.id, []), key=lambda item: (item.position, item.id)):
            question_options = options_by_question.get(question.id, [])
            if question.option_source == "STATIC":
                visible_options = sorted(question_options, key=lambda item: (item.position, item.id))
            elif question.option_source == "ORG_CNPJ":
                visible_options = [
                    option
                    for option in sorted(question_options, key=lambda item: (item.position, item.id))
                    if option.code == "unknown" and option.label == "Não sei informar"
                ]
            else:
                visible_options = []

            questions.append(
                {
                    "question_number": question.question_number,
                    "code": question.code,
                    "question_type": question.question_type,
                    "text": question.text,
                    "helper_text": question.helper_text,
                    "placeholder": question.placeholder,
                    "low_label": question.low_label,
                    "high_label": question.high_label,
                    "required": bool(question.required),
                    "position": question.position,
                    "analysis_role": question.analysis_role,
                    "option_source": question.option_source,
                    "options": [
                        {
                            "code": option.code,
                            "label": option.label,
                            "position": option.position,
                            "score_value": option.score_value,
                            "is_exclusive": bool(option.is_exclusive),
                        }
                        for option in visible_options
                    ],
                }
            )

        sections.append(
            {
                "code": section.code,
                "title": section.title,
                "position": section.position,
                "analysis_type": section.analysis_type,
                "questions": questions,
            }
        )

    return {
        "code": data.survey.code,
        "title": data.survey.title,
        "intro_text": data.survey.intro_text,
        "completion_text": data.survey.completion_text,
        "status": data.survey.status,
        "version": data.survey.version,
        "sections": sections,
    }
