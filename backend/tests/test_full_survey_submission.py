"""HTTP submission coverage built by reading the official seed, never executing SQL."""

import logging
import re
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user, get_db_session
from app.main import app
from app.models.anonymous_responses import (
    AnonymousResponse,
    AnonymousResponseSegment,
    ResponseAnswer,
    ResponseAnswerOption,
)
from app.models.participation import SurveyParticipation
from app.repositories import submission_repository
from app.services import survey_submission_service as submission_service
from app.services.organization_catalog import OrganizationCatalogService


SEED_PATH = Path(__file__).resolve().parents[1] / "sql" / "003_seed_climate_survey_2026.sql"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SURVEY_ID = 2026
SYNTHETIC_USER_ID = 900001
REGIONAL_SC_CASES = (
    ("MATRIZ", "MATRIZ"),
    ("BA", "AJU"),
    ("CE", "FOR"),
    ("GP", "ANA"),
    ("MG/SPN", "CGE"),
    ("PR", "SJS"),
    ("RJ", "SJM"),
    ("SPE", "GRU"),
    ("SPS", "BRE"),
    ("SR", "BNU"),
)
SYNTHETIC_TEXT = {
    "Q40": "Resposta fictícia: organizar as etapas da jornada.",
    "Q41": "Resposta fictícia: melhorar a comunicação entre as equipes.",
    "Q42": "Colaboração",
}


def _read_sql_values(expression, *, question_id=None):
    """Decode only the seed's literals and placeholders, with no SQL engine."""
    token_pattern = re.compile(
        r"\s*(?:'((?:''|[^'])*)'|(NULL)|(-?\d+)|(@survey_id|@question_id|section\.id))\s*(,|$)",
        re.DOTALL,
    )
    expression = expression.strip()
    values = []
    cursor = 0
    while cursor < len(expression):
        match = token_pattern.match(expression, cursor)
        assert match is not None, "Unsupported literal in the official seed"
        if match.group(1) is not None:
            value = match.group(1).replace("''", "'")
        elif match.group(2) is not None:
            value = None
        elif match.group(3) is not None:
            value = int(match.group(3))
        else:
            value = {
                "@survey_id": SURVEY_ID,
                "@question_id": question_id,
                "section.id": None,
            }[match.group(4)]
        values.append(value)
        cursor = match.end()
    return values


@pytest.fixture(scope="module")
def official_definition():
    seed = SEED_PATH.read_text(encoding="utf-8")
    survey_code = re.search(
        r"SET @survey_id = \(SELECT id FROM surveys WHERE code = '([^']+)'\);", seed
    ).group(1)
    question_pattern = re.compile(
        r"INSERT INTO survey_questions \((?P<columns>[^)]+)\)\s*"
        r"SELECT (?P<values>.*?)\s*FROM survey_sections AS section\s*"
        r"WHERE section\.survey_id = @survey_id AND section\.code = '(?P<section>[^']+)'"
        r"(?P<remainder>.*?)(?=INSERT INTO survey_questions|\Z)",
        re.DOTALL,
    )
    option_pattern = re.compile(
        r"INSERT INTO survey_question_options \((?P<columns>[^)]+)\)\s*"
        r"VALUES\s*(?P<rows>.*?)\s*ON DUPLICATE KEY UPDATE",
        re.DOTALL,
    )
    row_pattern = re.compile(r"\(((?:'(?:''|[^'])*'|[^()'])+)\)")
    questions = []
    options = []
    for match in question_pattern.finditer(seed):
        columns = [column.strip() for column in match.group("columns").split(",")]
        values = _read_sql_values(match.group("values"))
        assert len(columns) == len(values)
        attributes = dict(zip(columns, values))
        # IDs are deliberately unrelated to frontend Qxx codes and are never submitted.
        attributes["id"] = 1000 + attributes["question_number"]
        attributes["required"] = bool(attributes["required"])
        attributes["section_code"] = match.group("section")
        question = SimpleNamespace(**attributes)
        questions.append(question)
        for option_match in option_pattern.finditer(match.group("remainder")):
            option_columns = [column.strip() for column in option_match.group("columns").split(",")]
            rows = row_pattern.findall(option_match.group("rows"))
            assert rows, "The official option insert must contain literal rows"
            for row in rows:
                option_values = _read_sql_values(row, question_id=question.id)
                assert len(option_columns) == len(option_values)
                option_attributes = dict(zip(option_columns, option_values))
                option_attributes["id"] = 10000 + len(options)
                option_attributes["is_exclusive"] = bool(option_attributes["is_exclusive"])
                options.append(SimpleNamespace(**option_attributes))
    section_count = len(re.findall(r"INSERT INTO survey_sections", seed))
    assert section_count == 13, "The official survey must retain all sections"
    assert len(questions) == 41, "The fixture must use all active official questions"
    return SimpleNamespace(code=survey_code, section_count=section_count, questions=questions, options=options)


class FakeSession:
    """Persist model objects only in memory; any accidental database read fails."""

    def __init__(self):
        self.active = True
        self.added = []
        self.committed = []
        self.commit_count = 0
        self.rollback_count = 0
        self.next_answer_id = 5000

    def in_transaction(self):
        return self.active

    def begin(self):
        self.active = True
        return self

    def add(self, row):
        self.added.append(row)

    def flush(self):
        for row in self.added:
            if isinstance(row, ResponseAnswer) and row.id is None:
                row.id = self.next_answer_id
                self.next_answer_id += 1

    def commit(self):
        self.committed.extend(self.added)
        self.added.clear()
        self.commit_count += 1
        self.active = False

    def rollback(self):
        self.added.clear()
        self.rollback_count += 1
        self.active = False

    def execute(self, *args, **kwargs):
        raise AssertionError("This test must never execute SQL")

    scalar = execute
    scalars = execute


class RecordingOrganizationCatalog(OrganizationCatalogService):
    def __init__(self):
        self.calls = []

    def validate_selection(self, option_source, option_code, *, regional_code=None, base_code=None):
        self.calls.append((option_source, option_code, regional_code, base_code))
        return super().validate_selection(
            option_source, option_code, regional_code=regional_code, base_code=base_code
        )


def frontend_payload(definition, regional, sc):
    """Match SurveyFlow: uppercase question ID and string option values."""
    payload = []
    for question in definition.questions:
        question_code = question.code.upper()
        available = sorted(
            [option for option in definition.options if option.question_id == question.id],
            key=lambda option: option.position,
        )
        if question.option_source == "ORG_REGIONAL":
            codes = [regional]
        elif question.option_source == "ORG_BASE":
            codes = [sc]
        elif question.code == "Q03":
            codes = ["OPERATIONAL"]
        elif question.question_type in {"TEXTAREA", "SHORT_TEXT"}:
            payload.append({"question_code": question_code, "text_value": SYNTHETIC_TEXT[question_code]})
            continue
        elif question.question_type == "MULTIPLE_CHOICE":
            codes = [option.code for option in available if not option.is_exclusive][:2]
        elif question.question_type in {"LIKERT", "NPS"}:
            codes = [available[-1].code]
        else:
            codes = [available[0].code]
        payload.append({"question_code": question_code, "option_codes": [str(code) for code in codes]})
    return {"answers": payload}


@pytest.fixture
def full_submission_http(monkeypatch, official_definition):
    session = FakeSession()
    catalog = RecordingOrganizationCatalog()
    current_survey = SimpleNamespace(id=SURVEY_ID, code=official_definition.code, status="ACTIVE")
    # ACTIVE exists only in this in-memory fixture; the real DRAFT seed is not altered.
    monkeypatch.setattr(submission_repository, "get_survey_by_code", lambda db, code: current_survey)
    monkeypatch.setattr(submission_repository, "get_participation", lambda db, sid, uid: None)
    monkeypatch.setattr(submission_repository, "get_questions_by_survey", lambda db, sid: official_definition.questions)
    monkeypatch.setattr(submission_repository, "get_options_by_question_ids", lambda db, ids: official_definition.options)
    monkeypatch.setattr(submission_service, "organization_catalog_service", catalog)
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=SYNTHETIC_USER_ID, access_type="EXTERNAL"
    )
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        with TestClient(app) as http:
            yield http, session, catalog
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_official_seed_fixture_retains_real_question_and_option_contract(official_definition):
    questions = official_definition.questions
    by_code = {question.code: question for question in questions}
    assert official_definition.section_count == 13
    assert len(questions) == 41
    assert [question.question_number for question in questions] == list(range(1, 42))
    expected_codes = (
        [f"Q{number:02d}" for number in range(1, 16)]
        + ["Q24"]
        + [f"Q{number:02d}" for number in range(16, 24)]
        + [f"Q{number:02d}" for number in range(25, 33)]
        + [f"Q{number:02d}" for number in range(34, 43)]
    )
    assert [question.code for question in questions] == expected_codes
    assert len({question.code for question in questions}) == 41
    assert len({question.question_number for question in questions}) == 41
    assert [question.question_number for question in questions] == list(range(1, 42))

    expected_display_numbers = {
        **{f"Q{number:02d}": number for number in range(1, 16)},
        "Q24": 16,
        **{f"Q{number:02d}": number + 1 for number in range(16, 24)},
        **{f"Q{number:02d}": number for number in range(25, 33)},
        **{f"Q{number:02d}": number - 1 for number in range(34, 43)},
    }
    assert {question.code: question.question_number for question in questions} == expected_display_numbers
    assert by_code["Q07"].text == "Consigo realizar minhas atividades dentro da minha jornada normal de trabalho."
    assert by_code["Q08"].text == "Nos últimos meses, com que frequência você trabalhou além de sua carga horária regular?"
    assert by_code["Q09"].text == "Quando você trabalha além do seu horário regular, na sua visão, qual costuma ser o principal motivo?"
    assert by_code["Q13"].text == "Minha liderança compartilha decisões e temas que afetam minhas atividades?"
    assert by_code["Q30"].text == "As pessoas são encorajadas a equilibrar sua vida profissional e pessoal."
    assert by_code["Q08"].question_type == by_code["Q09"].question_type == "SINGLE_CHOICE"
    options_by_code = lambda code: [option.label for option in sorted(
        (option for option in official_definition.options if option.question_id == by_code[code].id),
        key=lambda option: option.position,
    )]
    assert options_by_code("Q08") == ["Nunca", "Raramente", "Algumas vezes no mês", "Algumas vezes na semana", "Quase todos os dias"]
    assert options_by_code("Q09") == [
        "Volume elevado de trabalho", "Falta de pessoas na equipe",
        "Prazos ou metas difíceis de cumprir dentro da jornada",
        "Problemas em sistemas, ferramentas ou equipamentos", "Falta de organização ou planejamento",
        "Dependência de outras áreas ou processos", "Solicitações ou demandas da liderança",
        "Necessidade da operação", "Retrabalho ou falhas nos processos", "Outro motivo",
        "Minha jornada normalmente não se estende",
    ]
    assert (by_code["Q24"].question_number, by_code["Q24"].section_code, by_code["Q24"].position) == (16, "LIDERANCA", 6)
    assert by_code["Q24"].text == "Percebo que minha liderança atua de forma ética e coerente com as regras da empresa."
    assert by_code["Q24"].analysis_role == "SCORE" and by_code["Q24"].question_type == "LIKERT"
    assert {
        code: (by_code[code].question_number, by_code[code].section_code, by_code[code].position)
        for code in ("Q16", "Q17", "Q18", "Q19", "Q20", "Q21", "Q22", "Q23")
    } == {
        "Q16": (17, "AMBIENTE", 1), "Q17": (18, "AMBIENTE", 2),
        "Q18": (19, "AMBIENTE", 3), "Q19": (20, "AMBIENTE", 4),
        "Q20": (21, "AMBIENTE", 5), "Q21": (22, "ETICA", 1),
        "Q22": (23, "ETICA", 2), "Q23": (24, "ETICA", 3),
    }
    assert by_code["Q23"].text == "Sinto segurança para realizar um relato ou denúncia sem medo de sofrer retaliação ou consequências negativas."
    assert "Q33" not in by_code
    assert sum("sanitários" in question.text.lower() for question in questions) == 1
    assert by_code["Q32"].text == (
        "Os sanitários da unidade são mantidos em condições de higiene, "
        "conservados e em bom estado de funcionamento?"
    )
    assert [(by_code[code].question_number, by_code[code].position) for code in ("Q32", "Q34", "Q35")] == [
        (32, 1), (33, 2), (34, 3)
    ]
    assert by_code["Q39"].question_number == 38
    assert by_code["Q40"].question_number == 39
    assert by_code["Q41"].question_number == 40
    assert by_code["Q42"].question_number == 41
    manual_sql = (PROJECT_ROOT / "backend" / "sql" / "manual" / "unify_climate_2026_questions_32_33.sql").read_text(encoding="utf-8")
    assert "SET question_number = 0" in manual_sql
    assert not re.search(r"\bDELETE\s+FROM\s+(survey_questions|response_answers)", manual_sql, re.IGNORECASE)
    assert {question.code for question in questions if not question.required} == {"Q40", "Q41", "Q42"}
    assert [by_code[code].option_source for code in ("Q01", "Q02", "Q03")] == [
        "ORG_REGIONAL", "ORG_BASE", "STATIC"
    ]
    assert by_code["Q03"].question_type == "SINGLE_CHOICE"
    assert by_code["Q03"].text == "Seu perfil de atuação é:"
    assert by_code["Q01"].text == "Qual é a sua Regional?"
    assert by_code["Q06"].question_type == "MULTIPLE_CHOICE"
    assert by_code["Q39"].question_type == "NPS"
    assert by_code["Q42"].question_type == "SHORT_TEXT"
    assert by_code["Q39"].low_label == "Não recomendaria"
    assert by_code["Q39"].high_label == "Recomendaria com certeza"
    assert {case[0] for case in REGIONAL_SC_CASES} == set(OrganizationCatalogService().get_regionals())
    assert not any(option.question_id in {by_code["Q01"].id, by_code["Q02"].id} for option in official_definition.options)
    q3_options = [option for option in official_definition.options if option.question_id == by_code["Q03"].id]
    assert [(option.code, option.label) for option in q3_options] == [
        ("OPERATIONAL", "Operacional"), ("ADMINISTRATIVE", "Administrativo")
    ]
    q6_options = [option for option in official_definition.options if option.question_id == by_code["Q06"].id]
    assert len(q6_options) == 9
    assert [(option.code, option.is_exclusive) for option in q6_options][-1] == ("OPT_09", True)
    q39_options = [option for option in official_definition.options if option.question_id == by_code["Q39"].id]
    assert [option.code for option in q39_options] == [str(score) for score in range(11)]


def test_frontend_sources_and_chinese_translation_match_the_41_active_codes(official_definition):
    mock_source = (PROJECT_ROOT / "src" / "data" / "mockSurvey.ts").read_text(encoding="utf-8")
    mock_questions = re.findall(r'\{ id: "q(\d+)", number: (\d+),', mock_source)
    assert len(mock_questions) == 41
    assert [int(number) for _code, number in mock_questions] == list(range(1, 42))
    expected_visual_codes = [
        *range(1, 16), 24, *range(16, 24), *range(25, 33), *range(34, 43)
    ]
    assert [int(code) for code, _number in mock_questions] == expected_visual_codes
    assert {int(code): int(number) for code, number in mock_questions} == dict(
        zip(expected_visual_codes, range(1, 42))
    )
    assert re.search(r'id: "q24", number: 16, sectionId: "lideranca"', mock_source)
    management_source = (PROJECT_ROOT / "src" / "data" / "mockManagement.ts").read_text(encoding="utf-8")
    assert 'questionNumbers: [11, 12, 13, 14, 15, 16]' in management_source
    assert 'questionNumbers: [17, 18, 19, 20, 21]' in management_source
    assert 'questionNumbers: [22, 23, 24]' in management_source
    assert (
        'id: "q32", number: 32, sectionId: "condicoes-ambiente", type: "likert", '
        'text: "Os sanitários da unidade são mantidos em condições de higiene, '
        'conservados e em bom estado de funcionamento?", required: true'
    ) in mock_source

    chinese_source = (PROJECT_ROOT / "src" / "i18n" / "survey.zh.ts").read_text(encoding="utf-8")
    question_map = re.search(
        r"const questions: Record<string, QuestionTranslation> = \{(?P<body>.*?)\n\};",
        chinese_source,
        re.DOTALL,
    )
    assert question_map is not None
    translated_codes = re.findall(r"^\s*Q(\d{2}):", question_map.group("body"), re.MULTILINE)
    active_codes = [question.code.removeprefix("Q") for question in official_definition.questions]
    assert len(translated_codes) == len(set(translated_codes)) == 41
    assert set(translated_codes) == set(active_codes)
    assert 'Q32: { text: "本单位的卫生间保持卫生、设施完好且运行正常吗？" }' in question_map.group("body")
    assert not re.search(r"^\s*Q33:", question_map.group("body"), re.MULTILINE)
    assert 'Q07: { text: "我能够在正常工作时间内完成自己的工作。" }' in question_map.group("body")
    assert 'Q08: { text: "最近几个月，您有多频繁地超出规定工作时间工作？"' in question_map.group("body")
    assert 'Q09: { text: "当您超出正常工作时间工作时，您认为通常的主要原因是什么？"' in question_map.group("body")
    assert 'Q13: { text: "我的领导会分享影响我工作的决定和事项吗？" }' in question_map.group("body")
    assert 'Q24: { text: "我认为我的领导行事合乎道德，并遵守公司的规定。" }' in question_map.group("body")
    assert 'Q23: { text: "我可以放心举报，不必担心遭到报复或受到负面影响。" }' in question_map.group("body")
    assert 'Q30: { text: "大家会受到鼓励，在工作与个人生活之间保持平衡。" }' in question_map.group("body")
    q08_translation = re.search(r"Q08:.*?options: \{(?P<options>[^}]+)\}", question_map.group("body"))
    assert q08_translation is not None
    assert re.findall(r'OPT_\d{2}: "([^"]+)"', q08_translation.group("options")) == [
        "从不", "很少", "每月几次", "每周几次", "几乎每天"
    ]
    q09_translation = re.search(r"Q09:.*?options: \{(?P<options>.*?)\n  \} \},", question_map.group("body"), re.DOTALL)
    assert q09_translation is not None
    assert re.findall(r'OPT_\d{2}: "([^"]+)"', q09_translation.group("options")) == [
        "工作量过大", "团队人手不足", "期限或目标难以在正常工作时间内完成",
        "系统、工具或设备出现问题", "组织或计划不足", "依赖其他部门或流程",
        "领导提出的要求或任务", "运营需要", "流程返工或错误", "其他原因",
        "我的工作时间通常不会延长",
    ]


def test_manual_revision_sql_is_guarded_and_preserves_historical_answers():
    manual_sql = (PROJECT_ROOT / "backend" / "sql" / "manual" / "revise_climate_2026_question_order_and_texts.sql").read_text(encoding="utf-8")
    executable_sql = "\n".join(line for line in manual_sql.splitlines() if not line.lstrip().startswith("--"))
    assert "START TRANSACTION;" in executable_sql
    assert not re.search(r"(?im)^\s*COMMIT\s*;", executable_sql)
    assert "@preflight_ok = 1" in executable_sql
    assert "@approve_historical_prompt_reclassification = 0" in executable_sql
    assert "@shifted_rows = 9" in executable_sql
    assert "question_number = question_number + 1000" in executable_sql
    assert "@source_answer_count = @final_answer_count" in executable_sql
    assert not re.search(r"\bDELETE\s+FROM\s+(survey_questions|response_answers)", executable_sql, re.IGNORECASE)
    assert not re.search(r"\bUPDATE\s+response_answers\b", executable_sql, re.IGNORECASE)
    assert "Q03" in executable_sql and "Q32" in executable_sql and "Q33" in executable_sql


@pytest.mark.parametrize("regional,sc", REGIONAL_SC_CASES, ids=[regional for regional, _ in REGIONAL_SC_CASES])
def test_http_accepts_all_41_official_answers_for_every_regional(
    regional, sc, official_definition, full_submission_http, caplog
):
    http, session, catalog = full_submission_http
    payload = frontend_payload(official_definition, regional, sc)
    by_code = {answer["question_code"]: answer for answer in payload["answers"]}
    assert len(payload["answers"]) == 41
    assert by_code["Q01"] == {"question_code": "Q01", "option_codes": [regional]}
    assert by_code["Q02"] == {"question_code": "Q02", "option_codes": [sc]}
    assert by_code["Q03"] == {"question_code": "Q03", "option_codes": ["OPERATIONAL"]}
    assert by_code["Q06"]["option_codes"] == ["OPT_01", "OPT_02"]
    assert by_code["Q39"]["option_codes"] == ["10"]
    assert all(set(answer) in ({"question_code", "option_codes"}, {"question_code", "text_value"}) for answer in payload["answers"])

    with caplog.at_level(logging.INFO, logger=submission_service.__name__):
        response = http.post(f"/api/surveys/{official_definition.code}/responses", json=payload)

    assert response.status_code == 201, response.json()
    assert response.json() == {"submitted": True}
    assert session.commit_count == 1
    assert session.rollback_count == 0
    rows = session.committed
    answers = [row for row in rows if isinstance(row, ResponseAnswer)]
    assert len(answers) == 41
    assert {row.question_id for row in answers} == {question.id for question in official_definition.questions}
    question_by_code = {question.code: question for question in official_definition.questions}
    answer_by_question = {row.question_id: row for row in answers}
    for question in official_definition.questions:
        selected = [
            row for row in rows
            if isinstance(row, ResponseAnswerOption) and row.question_id == question.id
        ]
        if question.option_source in {"ORG_REGIONAL", "ORG_BASE"} or question.question_type in {"TEXTAREA", "SHORT_TEXT"}:
            assert selected == []
            continue
        expected_option_ids = [
            next(option.id for option in official_definition.options if option.question_id == question.id and option.code == code)
            for code in by_code[question.code]["option_codes"]
        ]
        assert [row.option_id for row in selected] == expected_option_ids
        assert all(row.answer_id == answer_by_question[question.id].id for row in selected)
    assert answer_by_question[question_by_code["Q01"].id].text_value == regional
    assert answer_by_question[question_by_code["Q02"].id].text_value == sc
    for code, text in SYNTHETIC_TEXT.items():
        assert answer_by_question[question_by_code[code].id].text_value == text
        assert text not in response.text
        assert text not in caplog.text

    q3 = question_by_code["Q03"]
    q3_option = next(option for option in official_definition.options if option.question_id == q3.id)
    assert answer_by_question[q3.id].text_value is None
    assert [row.option_id for row in rows if isinstance(row, ResponseAnswerOption) and row.question_id == q3.id] == [q3_option.id]
    assert {row.segment_type: row.segment_code for row in rows if isinstance(row, AnonymousResponseSegment)} == {
        "REGIONAL": regional, "BASE": sc
    }
    assert catalog.calls == [
        ("ORG_REGIONAL", regional, None, None),
        ("ORG_BASE", sc, regional, None),
    ]

    anonymous = [row for row in rows if isinstance(row, AnonymousResponse)]
    participation = [row for row in rows if isinstance(row, SurveyParticipation)]
    assert len(anonymous) == len(participation) == 1
    assert uuid.UUID(anonymous[0].response_id).version == 4
    assert {answer.response_id for answer in answers} == {anonymous[0].response_id}
    assert participation[0].user_id == SYNTHETIC_USER_ID
    assert participation[0].status == "COMPLETED"
    assert not hasattr(participation[0], "response_id")
    assert all(not hasattr(row, "user_id") and not hasattr(row, "participation_id") for row in rows if not isinstance(row, SurveyParticipation))
    assert anonymous[0].response_id not in response.text
    assert anonymous[0].response_id not in caplog.text
    assert str(SYNTHETIC_USER_ID) not in response.text
    assert str(SYNTHETIC_USER_ID) not in caplog.text


def test_http_rejects_archived_q33_when_a_client_still_submits_it(
    official_definition, full_submission_http
):
    http, session, _catalog = full_submission_http
    payload = frontend_payload(official_definition, "MG/SPN", "CGE")
    payload["answers"].append({"question_code": "Q33", "option_codes": ["1"]})

    response = http.post(f"/api/surveys/{official_definition.code}/responses", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "INVALID_ANSWER",
            "reason": "UNKNOWN_QUESTION",
        }
    }
    assert session.commit_count == 0
    assert session.rollback_count == 1
    assert session.added == [] and session.committed == []


@pytest.mark.parametrize(
    ("regional", "sc"),
    [("MATRIZ", "GRU"), ("SPS", "MATRIZ")],
)
def test_http_rejects_matriz_sc_outside_its_regional(
    regional, sc, official_definition, full_submission_http
):
    http, session, catalog = full_submission_http
    payload = frontend_payload(official_definition, regional, sc)

    response = http.post(f"/api/surveys/{official_definition.code}/responses", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "INVALID_OPTION",
            "question_code": "Q02",
            "reason": "SC_NOT_IN_REGIONAL",
        }
    }
    assert catalog.calls == [
        ("ORG_REGIONAL", regional, None, None),
        ("ORG_BASE", sc, regional, None),
    ]
    assert session.commit_count == 0
    assert session.rollback_count == 1
    assert session.added == [] and session.committed == []


@pytest.mark.parametrize("role", ["MANAGEMENT", "SURVEY_ADMIN", "ADMIN"])
def test_management_roles_without_collaborator_can_submit_once(role, official_definition, full_submission_http):
    http, session, _catalog = full_submission_http
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=SYNTHETIC_USER_ID, access_type="INTERNAL", status="ACTIVE", roles=(role,)
    )
    payload = frontend_payload(official_definition, "MG/SPN", "CGE")

    response = http.post(f"/api/surveys/{official_definition.code}/responses", json=payload)

    assert response.status_code == 201, response.json()
    assert response.json() == {"submitted": True}
    assert session.commit_count == 1
    assert session.rollback_count == 0
    participations = [row for row in session.committed if isinstance(row, SurveyParticipation)]
    assert len(participations) == 1
    assert participations[0].user_id == SYNTHETIC_USER_ID
    assert participations[0].status == "COMPLETED"

@pytest.mark.parametrize("variant", ["administrative_profile", "exclusive_choice", "nps_zero"])
def test_http_full_official_survey_accepts_work_profile_and_choice_variants(
    variant, official_definition, full_submission_http, caplog
):
    http, session, catalog = full_submission_http
    payload = frontend_payload(official_definition, "MG/SPN", "CGE")
    by_code = {answer["question_code"]: answer for answer in payload["answers"]}
    question_by_code = {question.code: question for question in official_definition.questions}
    if variant == "administrative_profile":
        by_code["Q03"]["option_codes"] = ["ADMINISTRATIVE"]
    elif variant == "nps_zero":
        by_code["Q39"]["option_codes"] = ["0"]
    else:
        q6 = question_by_code["Q06"]
        exclusive = next(option for option in official_definition.options if option.question_id == q6.id and option.is_exclusive)
        by_code["Q06"]["option_codes"] = [exclusive.code]
    assert len(payload["answers"]) == 41

    with caplog.at_level(logging.INFO, logger=submission_service.__name__):
        response = http.post(f"/api/surveys/{official_definition.code}/responses", json=payload)

    assert response.status_code == 201, response.json()
    assert response.json() == {"submitted": True}
    assert session.commit_count == 1 and session.rollback_count == 0
    answers = [row for row in session.committed if isinstance(row, ResponseAnswer)]
    assert len(answers) == 41
    if variant == "administrative_profile":
        q3 = question_by_code["Q03"]
        assert next(row for row in answers if row.question_id == q3.id).text_value is None
        q3_option = next(option for option in official_definition.options if option.question_id == q3.id and option.code == "ADMINISTRATIVE")
        selected_q3 = [row for row in session.committed if isinstance(row, ResponseAnswerOption) and row.question_id == q3.id]
        assert len(selected_q3) == 1 and selected_q3[0].option_id == q3_option.id
        assert {row.segment_type: row.segment_code for row in session.committed if isinstance(row, AnonymousResponseSegment)} == {
            "REGIONAL": "MG/SPN", "BASE": "CGE"
        }
    elif variant == "nps_zero":
        q39 = question_by_code["Q39"]
        zero_option = next(option for option in official_definition.options if option.question_id == q39.id and option.code == "0")
        selected = [row for row in session.committed if isinstance(row, ResponseAnswerOption) and row.question_id == q39.id]
        assert len(selected) == 1 and selected[0].option_id == zero_option.id
    else:
        selected = [row for row in session.committed if isinstance(row, ResponseAnswerOption) and row.question_id == q6.id]
        assert len(selected) == 1
        assert selected[0].option_id == exclusive.id
        assert {row.segment_type for row in session.committed if isinstance(row, AnonymousResponseSegment)} == {"REGIONAL", "BASE"}
    assert [call[0] for call in catalog.calls] == ["ORG_REGIONAL", "ORG_BASE"]
    for text in SYNTHETIC_TEXT.values():
        assert text not in response.text + caplog.text
