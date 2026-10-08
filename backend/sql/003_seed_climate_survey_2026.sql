-- Official questionnaire seed for manual review. Do not execute in this stage.
-- Source of section/question text, helper text, placeholders, required flags, types, NPS labels, and static choices: src/data/mockSurvey.ts.
-- No USE, CREATE DATABASE, demo regional/base options, or application startup execution.
-- Existing databases must use backend/sql/manual/unify_climate_2026_questions_32_33.sql; this seed does not archive historical Q33 rows.
-- Q1/Q2 use organization catalogs. Q3 is a static work-profile choice.
-- This survey is seeded as DRAFT. A human must explicitly approve and activate it later.

START TRANSACTION;

INSERT INTO surveys (code, title, intro_text, completion_text, status, version, starts_on, ends_on, min_group_size)
VALUES (
    'CLIMATE_2026',
    'Pesquisa de Clima Organizacional 2026',
    CONCAT(
    'Sua voz faz parte da nossa evolução.',
    CHAR(10),
    CHAR(10),
    'Queremos ouvir você e conhecer sua experiência na J&T Express.',
    CHAR(10),
    CHAR(10),
    'Esta pesquisa é um espaço para compartilhar, de forma sincera, suas percepções sobre o ambiente de trabalho, liderança, relações profissionais, condições de trabalho e outros aspectos que fazem parte do seu dia a dia.',
    CHAR(10),
    CHAR(10),
    'Suas respostas nos ajudarão a reconhecer o que estamos fazendo bem, identificar oportunidades de melhoria e direcionar ações concretas para construir um ambiente de trabalho cada vez mais respeitoso, seguro, saudável e positivo.',
    CHAR(10),
    CHAR(10),
    'A pesquisa é anônima e as respostas serão analisadas de forma consolidada, garantindo confidencialidade e liberdade para que você possa expressar sua percepção com transparência.',
    CHAR(10),
    CHAR(10),
    'Participe com sinceridade.',
    CHAR(10),
    CHAR(10),
    'Cada percepção contribui para entendermos melhor a realidade das nossas equipes e construirmos, juntos, os próximos passos.',
    CHAR(10),
    CHAR(10),
    'Escutar para entender.',
    CHAR(10),
    'Entender para agir.',
    CHAR(10),
    'Evoluir juntos.'
),
    'Obrigada por participar!',
    'DRAFT', 1, NULL, NULL, 5
)
ON DUPLICATE KEY UPDATE
    intro_text = VALUES(intro_text),
    completion_text = VALUES(completion_text);
SET @survey_id = (SELECT id FROM surveys WHERE code = 'CLIMATE_2026');

-- Sections retain the exact labels and order from mockSurvey.ts.
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'IDENTIFICACAO', 'IDENTIFICAÇÃO DA OPERAÇÃO', 1, 'SEGMENT')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'CONDICOES', 'CONDIÇÕES E ORGANIZAÇÃO DO TRABALHO', 2, 'MIXED')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'JORNADA', 'JORNADA DE TRABALHO', 3, 'MIXED')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'LIDERANCA', 'LIDERANÇA E COMUNICAÇÃO', 4, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'AMBIENTE', 'AMBIENTE, RESPEITO E SEGURANÇA', 5, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'ETICA', 'ÉTICA E COMPLIANCE', 6, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'DESENVOLVIMENTO', 'RECONHECIMENTO E DESENVOLVIMENTO', 7, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'REMUNERACAO', 'REMUNERAÇÃO E BENEFÍCIOS', 8, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'SAUDE', 'SAÚDE, BEM-ESTAR E EQUILÍBRIO', 9, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'CONDICOES_AMBIENTE', 'AMBIENTE E CONDIÇÕES DE TRABALHO', 10, 'SCORE')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'PERMANENCIA', 'PERMANÊNCIA E VÍNCULO COM A EMPRESA', 11, 'MIXED')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'PERCEPCAO', 'PERCEPÇÃO GERAL', 12, 'NPS')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);
INSERT INTO survey_sections (survey_id, code, title, position, analysis_type)
VALUES (@survey_id, 'SUA_VOZ', 'SUA VOZ', 13, 'OPEN_TEXT')
ON DUPLICATE KEY UPDATE title = VALUES(title), position = VALUES(position), analysis_type = VALUES(analysis_type);

-- Questions and fixed choices are seeded in their official display order.
INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 1, 'Q01', 'SELECT', 'Qual é a sua Regional?', NULL, 'Selecionar Regional', NULL, NULL, 1, 1, 'SEGMENT', 'ORG_REGIONAL'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'IDENTIFICACAO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q01');
INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 2, 'Q02', 'SELECT', 'Qual é a sua Base/Unidade de atuação?', NULL, 'Selecionar Base/Unidade', NULL, NULL, 1, 2, 'SEGMENT', 'ORG_BASE'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'IDENTIFICACAO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q02');
INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 3, 'Q03', 'SINGLE_CHOICE', 'Seu perfil de atuação é:', NULL, NULL, NULL, NULL, 1, 3, 'CATEGORY', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'IDENTIFICACAO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q03');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, 'OPERATIONAL', 'Operacional', 1, NULL, 0),
    (@question_id, 'ADMINISTRATIVE', 'Administrativo', 2, NULL, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 4, 'Q04', 'LIKERT', 'Tenho estrutura, ferramentas e recursos adequados para realizar meu trabalho.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'CONDICOES'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q04');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 5, 'Q05', 'LIKERT', 'Os processos internos e a organização do trabalho facilitam a realização das minhas atividades.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'CONDICOES'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q05');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 6, 'Q06', 'MULTIPLE_CHOICE', 'Em relação à estrutura e aos recursos disponíveis para o seu trabalho, o que você considera que precisa ser melhorado?', 'Você pode selecionar mais de uma opção.', NULL, NULL, NULL, 1, 3, 'CATEGORY', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'CONDICOES'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q06');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, 'OPT_01', 'Espaço ou posto de trabalho', 1, NULL, 0),
    (@question_id, 'OPT_02', 'Mesa, cadeira ou mobiliário', 2, NULL, 0),
    (@question_id, 'OPT_03', 'Computador ou notebook', 3, NULL, 0),
    (@question_id, 'OPT_04', 'Monitor, mouse, teclado, headset ou outros acessórios', 4, NULL, 0),
    (@question_id, 'OPT_05', 'Estado de conservação dos equipamentos', 5, NULL, 0),
    (@question_id, 'OPT_06', 'Manutenção ou substituição de equipamentos', 6, NULL, 0),
    (@question_id, 'OPT_07', 'Sistemas ou ferramentas de trabalho', 7, NULL, 0),
    (@question_id, 'OPT_08', 'Outro', 8, NULL, 0),
    (@question_id, 'OPT_09', 'Não identifico necessidade de melhoria', 9, NULL, 1)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 7, 'Q07', 'LIKERT', 'Na maior parte dos dias, consigo realizar minhas atividades dentro da minha jornada normal de trabalho.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'JORNADA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q07');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 8, 'Q08', 'SINGLE_CHOICE', 'Trabalhar além da jornada normal, isso acontece com que frequência?', NULL, NULL, NULL, NULL, 1, 2, 'CATEGORY', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'JORNADA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q08');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, 'OPT_01', 'Nunca', 1, NULL, 0),
    (@question_id, 'OPT_02', 'Raramente', 2, NULL, 0),
    (@question_id, 'OPT_03', 'Algumas vezes no mês', 3, NULL, 0),
    (@question_id, 'OPT_04', 'Algumas vezes na semana', 4, NULL, 0),
    (@question_id, 'OPT_05', 'Quase todos os dias', 5, NULL, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 9, 'Q09', 'SINGLE_CHOICE', 'Quando minha jornada de trabalho se estende, qual é o principal motivo?', NULL, NULL, NULL, NULL, 1, 3, 'CATEGORY', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'JORNADA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q09');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, 'OPT_01', 'Volume elevado de trabalho', 1, NULL, 0),
    (@question_id, 'OPT_02', 'Falta de pessoas na equipe', 2, NULL, 0),
    (@question_id, 'OPT_03', 'Prazos ou metas difíceis de cumprir dentro da jornada', 3, NULL, 0),
    (@question_id, 'OPT_04', 'Problemas em sistemas, ferramentas ou equipamentos', 4, NULL, 0),
    (@question_id, 'OPT_05', 'Falta de organização ou planejamento', 5, NULL, 0),
    (@question_id, 'OPT_06', 'Dependência de outras áreas ou processos', 6, NULL, 0),
    (@question_id, 'OPT_07', 'Solicitações ou demandas da liderança', 7, NULL, 0),
    (@question_id, 'OPT_08', 'Necessidade da operação', 8, NULL, 0),
    (@question_id, 'OPT_09', 'Retrabalho ou falhas nos processos', 9, NULL, 0),
    (@question_id, 'OPT_10', 'Outro motivo', 10, NULL, 0),
    (@question_id, 'OPT_11', 'Minha jornada normalmente não se estende', 11, NULL, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 10, 'Q10', 'SINGLE_CHOICE', 'Na sua opinião, o que mais ajudaria a reduzir situações de jornada excessiva na sua área?', NULL, NULL, NULL, NULL, 1, 4, 'CATEGORY', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'JORNADA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q10');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, 'OPT_01', 'Melhor planejamento e organização das atividades', 1, NULL, 0),
    (@question_id, 'OPT_02', 'Aumento do número de pessoas na equipe', 2, NULL, 0),
    (@question_id, 'OPT_03', 'Melhor distribuição das atividades', 3, NULL, 0),
    (@question_id, 'OPT_04', 'Melhoria dos sistemas e ferramentas', 4, NULL, 0),
    (@question_id, 'OPT_05', 'Revisão de metas e prazos', 5, NULL, 0),
    (@question_id, 'OPT_06', 'Melhor organização e integração entre as áreas', 6, NULL, 0),
    (@question_id, 'OPT_07', 'Redução de retrabalho', 7, NULL, 0),
    (@question_id, 'OPT_08', 'Maior acompanhamento da liderança sobre a jornada', 8, NULL, 0),
    (@question_id, 'OPT_09', 'Melhor definição de prioridades', 9, NULL, 0),
    (@question_id, 'OPT_10', 'Outra ação', 10, NULL, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 11, 'Q11', 'LIKERT', 'Minha liderança me trata com respeito, profissionalismo e imparcialidade.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'LIDERANCA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q11');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 12, 'Q12', 'LIKERT', 'Recebo orientações claras sobre minhas responsabilidades, prioridades e o que é esperado do meu trabalho.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'LIDERANCA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q12');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 13, 'Q13', 'LIKERT', 'Minha liderança compartilha informações importantes e mudanças que impactam meu trabalho.', NULL, NULL, NULL, NULL, 1, 3, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'LIDERANCA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q13');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 14, 'Q14', 'LIKERT', 'Tenho abertura para procurar minha liderança quando preciso tirar dúvidas, apresentar dificuldades ou pedir orientação.', NULL, NULL, NULL, NULL, 1, 4, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'LIDERANCA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q14');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 15, 'Q15', 'LIKERT', 'Recebo feedbacks constantemente da minha liderança referente o trabalho que realizo.', NULL, NULL, NULL, NULL, 1, 5, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'LIDERANCA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q15');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 16, 'Q16', 'LIKERT', 'Sinto que trabalho em um ambiente respeitoso, colaborativo e com apoio entre as pessoas.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q16');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 17, 'Q17', 'LIKERT', 'Sinto-me seguro(a) física e emocionalmente no meu ambiente de trabalho.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q17');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 18, 'Q18', 'LIKERT', 'Sinto que a empresa mantém um ambiente de trabalho livre de assédio e discriminação.', NULL, NULL, NULL, NULL, 1, 3, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q18');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 19, 'Q19', 'LIKERT', 'Percebo que as pessoas são tratadas com respeito e justiça, independentemente de suas características pessoais.', NULL, NULL, NULL, NULL, 1, 4, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q19');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 20, 'Q20', 'LIKERT', 'Sinto segurança para expressar opiniões, dúvidas ou dificuldades relacionadas ao meu trabalho.', NULL, NULL, NULL, NULL, 1, 5, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q20');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 21, 'Q21', 'LIKERT', 'Conheço o Canal de Denúncias Benfen e sei como utilizá-lo caso seja necessário.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'ETICA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q21');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 22, 'Q22', 'LIKERT', 'Confio que uma situação relatada pelo Canal de Denúncias Benfen será tratada de forma adequada e imparcial.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'ETICA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q22');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 23, 'Q23', 'LIKERT', 'Sinto segurança para realizar um relato ou denúncia sem medo de sofrer retaliação ou consequências negativas.', NULL, NULL, NULL, NULL, 1, 3, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'ETICA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q23');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 24, 'Q24', 'LIKERT', 'Percebo que minha liderança atua de forma ética e coerente com as regras da empresa.', NULL, NULL, NULL, NULL, 1, 4, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'ETICA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q24');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 25, 'Q25', 'LIKERT', 'Sinto que meu trabalho e minhas entregas são reconhecidos.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'DESENVOLVIMENTO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q25');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 26, 'Q26', 'LIKERT', 'Consigo visualizar oportunidades de desenvolvimento e crescimento profissional na empresa.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'DESENVOLVIMENTO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q26');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 27, 'Q27', 'LIKERT', 'Considero minha remuneração compatível com minhas atividades e responsabilidades.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'REMUNERACAO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q27');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 28, 'Q28', 'LIKERT', 'Considero que os benefícios oferecidos pela empresa atendem às minhas necessidades.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'REMUNERACAO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q28');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 29, 'Q29', 'LIKERT', 'Percebo que a empresa se preocupa com a saúde, o bem-estar e as condições de trabalho dos colaboradores.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'SAUDE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q29');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 30, 'Q30', 'LIKERT', 'Consigo manter um equilíbrio adequado entre minha vida profissional e pessoal.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'SAUDE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q30');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 31, 'Q31', 'LIKERT', 'Sei onde buscar apoio ou orientação dentro da empresa quando enfrento alguma dificuldade relacionada ao trabalho.', NULL, NULL, NULL, NULL, 1, 3, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'SAUDE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q31');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 32, 'Q32', 'LIKERT', 'Os sanitários da unidade são mantidos em condições de higiene, conservados e em bom estado de funcionamento?', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'CONDICOES_AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q32');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 33, 'Q34', 'LIKERT', 'O espaço disponível para realizar as refeições é adequado à quantidade de colaboradores.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'CONDICOES_AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q34');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 34, 'Q35', 'LIKERT', 'Os equipamentos disponíveis para apoio às refeições, como micro-ondas e geladeira, são adequados às necessidades dos colaboradores.', NULL, NULL, NULL, NULL, 1, 3, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'CONDICOES_AMBIENTE'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q35');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 35, 'Q36', 'LIKERT', 'Pretendo continuar trabalhando na J&T Express nos próximos 12 meses.', NULL, NULL, NULL, NULL, 1, 1, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'PERMANENCIA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q36');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 36, 'Q37', 'LIKERT', 'Tenho orgulho de trabalhar na J&T Express.', NULL, NULL, NULL, NULL, 1, 2, 'SCORE', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'PERMANENCIA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q37');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '1', 'Discordo totalmente', 1, 1, 0),
    (@question_id, '2', 'Discordo', 2, 2, 0),
    (@question_id, '3', 'Nem concordo nem discordo', 3, 3, 0),
    (@question_id, '4', 'Concordo', 4, 4, 0),
    (@question_id, '5', 'Concordo totalmente', 5, 5, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 37, 'Q38', 'SINGLE_CHOICE', 'Qual fator que mais poderia influenciar na sua decisão de sair da empresa?', 'Escolha o principal.', NULL, NULL, NULL, 1, 3, 'CATEGORY', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'PERMANENCIA'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q38');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, 'OPT_01', 'Remuneração', 1, NULL, 0),
    (@question_id, 'OPT_02', 'Benefícios', 2, NULL, 0),
    (@question_id, 'OPT_03', 'Liderança/Gestão', 3, NULL, 0),
    (@question_id, 'OPT_04', 'Carga ou jornada de trabalho', 4, NULL, 0),
    (@question_id, 'OPT_05', 'Ambiente ou clima de trabalho', 5, NULL, 0),
    (@question_id, 'OPT_06', 'Falta de reconhecimento', 6, NULL, 0),
    (@question_id, 'OPT_07', 'Falta de oportunidade de crescimento', 7, NULL, 0),
    (@question_id, 'OPT_08', 'Estrutura ou condições de trabalho', 8, NULL, 0),
    (@question_id, 'OPT_09', 'Processos e organização do trabalho', 9, NULL, 0),
    (@question_id, 'OPT_10', 'Relacionamento com colegas/equipe', 10, NULL, 0),
    (@question_id, 'OPT_11', 'Distância/deslocamento', 11, NULL, 0),
    (@question_id, 'OPT_12', 'Atividade diferente da expectativa', 12, NULL, 0),
    (@question_id, 'OPT_13', 'Questões pessoais', 13, NULL, 0),
    (@question_id, 'OPT_14', 'Receber uma proposta melhor de outra empresa', 14, NULL, 0),
    (@question_id, 'OPT_15', 'Outro', 15, NULL, 0),
    (@question_id, 'OPT_16', 'No momento, não penso em sair da empresa', 16, NULL, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 38, 'Q39', 'NPS', 'Em uma escala de 0 a 10, o quanto você recomendaria a J&T Express como um bom lugar para trabalhar?', NULL, NULL, 'Não recomendaria', 'Recomendaria com certeza', 1, 1, 'NPS', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'PERCEPCAO'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q39');
INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
VALUES
    (@question_id, '0', '0', 1, 0, 0),
    (@question_id, '1', '1', 2, 1, 0),
    (@question_id, '2', '2', 3, 2, 0),
    (@question_id, '3', '3', 4, 3, 0),
    (@question_id, '4', '4', 5, 4, 0),
    (@question_id, '5', '5', 6, 5, 0),
    (@question_id, '6', '6', 7, 6, 0),
    (@question_id, '7', '7', 8, 7, 0),
    (@question_id, '8', '8', 9, 8, 0),
    (@question_id, '9', '9', 10, 9, 0),
    (@question_id, '10', '10', 11, 10, 0)
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 39, 'Q40', 'TEXTAREA', 'Que mudança ajudaria a organizar melhor a jornada de trabalho na sua área?', 'Resposta aberta. Opcional.', 'Escreva sua resposta (opcional)', NULL, NULL, 0, 1, 'OPEN_TEXT', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'SUA_VOZ'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q40');
INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 40, 'Q41', 'TEXTAREA', 'O que a empresa poderia melhorar para tornar sua experiência de trabalho melhor?', 'Resposta aberta. Opcional.', 'Escreva sua resposta (opcional)', NULL, NULL, 0, 2, 'OPEN_TEXT', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'SUA_VOZ'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q41');
INSERT INTO survey_questions (survey_id, section_id, question_number, code, question_type, text, helper_text, placeholder, low_label, high_label, required, position, analysis_role, option_source)
SELECT @survey_id, section.id, 41, 'Q42', 'SHORT_TEXT', 'O que você mais valoriza em trabalhar na J&T Express?', 'Responda em uma palavra. Opcional.', 'Uma palavra (opcional)', NULL, NULL, 0, 3, 'OPEN_TEXT', 'STATIC'
FROM survey_sections AS section
WHERE section.survey_id = @survey_id AND section.code = 'SUA_VOZ'
ON DUPLICATE KEY UPDATE section_id = VALUES(section_id), question_type = VALUES(question_type), text = VALUES(text), helper_text = VALUES(helper_text), placeholder = VALUES(placeholder), low_label = VALUES(low_label), high_label = VALUES(high_label), required = VALUES(required), position = VALUES(position), analysis_role = VALUES(analysis_role), option_source = VALUES(option_source);
SET @question_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q42');
-- Dynamic Q1/Q2 organization catalog values are intentionally not inserted by this official seed.
-- Q3 uses only its two static work-profile options and does not create an organizational segment.

COMMIT;
