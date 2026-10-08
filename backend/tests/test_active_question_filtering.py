from types import SimpleNamespace

from app.repositories import management_repository, submission_repository, survey_repository


class EmptyRows:
    def all(self):
        return []


class QueryRecorder:
    def __init__(self, survey=None):
        self.statements = []
        self.survey = survey or SimpleNamespace(id=2026)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def scalar(self, statement):
        self.statements.append(statement)
        return self.survey

    def scalars(self, statement):
        self.statements.append(statement)
        return EmptyRows()

    def execute(self, statement):
        self.statements.append(statement)
        return EmptyRows()


def compiled(statement):
    return str(statement.compile(compile_kwargs={"literal_binds": True}))


def test_survey_definition_and_submission_only_load_positive_question_numbers():
    submission_session = QueryRecorder()
    submission_repository.get_questions_by_survey(submission_session, 2026)
    assert "survey_questions.question_number > 0" in compiled(submission_session.statements[0])

    read_session = QueryRecorder()
    original_session_local = survey_repository.SessionLocal
    survey_repository.SessionLocal = lambda: read_session
    try:
        survey_repository.get_survey_by_code("CLIMATE_2026")
    finally:
        survey_repository.SessionLocal = original_session_local

    question_query = next(
        statement for statement in read_session.statements
        if "survey_questions" in compiled(statement)
    )
    assert "survey_questions.question_number > 0" in compiled(question_query)


def test_management_question_analytics_exclude_archived_question_numbers():
    question_queries = (
        management_repository.get_q39_score_counts,
        management_repository.get_pillar_definitions,
        management_repository.get_pillar_answer_score_counts,
        management_repository.get_pillar_respondent_counts,
        management_repository.get_attention_question_definitions,
        management_repository.get_attention_group_respondent_counts,
        management_repository.get_attention_score_counts,
        management_repository.get_attention_question_respondent_counts,
        management_repository.get_voice_question_definitions,
        management_repository.get_voice_respondent_counts,
        management_repository.get_voice_text_answers,
    )
    for query in question_queries:
        session = QueryRecorder()
        query(session, 2026)
        assert len(session.statements) == 1
        assert "survey_questions.question_number > 0" in compiled(session.statements[0]), query.__name__
