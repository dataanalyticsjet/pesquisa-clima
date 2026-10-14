-- MANUAL REVIEW ONLY. Do not execute automatically or as part of application startup.
-- Target: existing CLIMATE_2026 already has archived Q33 (question_number=0).
-- No question IDs/codes or answer rows are changed or deleted.
-- Q24 keeps its meaning/ID but its historical scores will move from ETICA to LIDERANCA in analytics.
-- The five text edits do not version response history; if old answers exist, reports will use the revised prompt.
-- Review those counts and approve that interpretation before enabling the guarded updates.
-- Inspect preflight/postflight results; if any check fails, issue ROLLBACK.
-- COMMIT is intentionally absent as executable SQL; after explicit approval, issue it manually.

START TRANSACTION;

SET @survey_id = (SELECT id FROM surveys WHERE code = 'CLIMATE_2026');
-- Leave 0 during review. Change to 1 only after approving historical prompt reclassification.
SET @approve_historical_prompt_reclassification = 0;
SET @leadership_section_id = (
    SELECT id FROM survey_sections WHERE survey_id = @survey_id AND code = 'LIDERANCA'
);

-- Inspect actual persistent IDs and metadata before making changes.
SELECT survey.id AS survey_id, survey.code AS survey_code, survey.status AS survey_status,
       question.id AS question_id, question.code AS question_code,
       question.question_number, section.code AS section_code, question.position,
       question.analysis_role, question.question_type, question.text
FROM surveys AS survey
JOIN survey_questions AS question ON question.survey_id = survey.id
JOIN survey_sections AS section
  ON section.id = question.section_id AND section.survey_id = question.survey_id
WHERE survey.code = 'CLIMATE_2026'
  AND (question.question_number > 0 OR question.code = 'Q33')
ORDER BY question.question_number, question.code;

SELECT COUNT(*) INTO @active_question_count
FROM survey_questions WHERE survey_id = @survey_id AND question_number > 0;
SELECT COUNT(*) INTO @expected_active_sequence_count
FROM survey_questions WHERE survey_id = @survey_id AND question_number BETWEEN 1 AND 41;
SELECT COUNT(*) INTO @survey_section_count
FROM survey_sections WHERE survey_id = @survey_id;
SELECT COUNT(*) INTO @q03_profile_count
FROM survey_questions
WHERE survey_id = @survey_id AND code = 'Q03' AND question_number = 3
  AND question_type = 'SINGLE_CHOICE' AND text = 'Seu perfil de atuação é:';
SELECT COUNT(*) INTO @q32_unified_count
FROM survey_questions
WHERE survey_id = @survey_id AND code = 'Q32' AND question_number = 32
  AND text = 'Os sanitários da unidade são mantidos em condições de higiene, conservados e em bom estado de funcionamento?';
SELECT COUNT(*) INTO @affected_question_count
FROM survey_questions WHERE survey_id = @survey_id
  AND code IN ('Q16','Q17','Q18','Q19','Q20','Q21','Q22','Q23','Q24');
SELECT COUNT(*) INTO @expected_old_layout_count
FROM survey_questions AS question
JOIN survey_sections AS section
  ON section.id = question.section_id AND section.survey_id = question.survey_id
WHERE question.survey_id = @survey_id AND (
    (question.code = 'Q16' AND question.question_number = 16 AND question.position = 1 AND section.code = 'AMBIENTE') OR
    (question.code = 'Q17' AND question.question_number = 17 AND question.position = 2 AND section.code = 'AMBIENTE') OR
    (question.code = 'Q18' AND question.question_number = 18 AND question.position = 3 AND section.code = 'AMBIENTE') OR
    (question.code = 'Q19' AND question.question_number = 19 AND question.position = 4 AND section.code = 'AMBIENTE') OR
    (question.code = 'Q20' AND question.question_number = 20 AND question.position = 5 AND section.code = 'AMBIENTE') OR
    (question.code = 'Q21' AND question.question_number = 21 AND question.position = 1 AND section.code = 'ETICA') OR
    (question.code = 'Q22' AND question.question_number = 22 AND question.position = 2 AND section.code = 'ETICA') OR
    (question.code = 'Q23' AND question.question_number = 23 AND question.position = 3 AND section.code = 'ETICA') OR
    (question.code = 'Q24' AND question.question_number = 24 AND question.position = 4 AND section.code = 'ETICA'
       AND question.text = 'Percebo que minha liderança atua de forma ética e coerente com as regras da empresa.')
);
SELECT COUNT(*) INTO @expected_old_text_count
FROM survey_questions
WHERE survey_id = @survey_id AND (
    (code = 'Q07' AND text = 'Na maior parte dos dias, consigo realizar minhas atividades dentro da minha jornada normal de trabalho.') OR
    (code = 'Q08' AND text = 'Trabalhar além da jornada normal, isso acontece com que frequência?') OR
    (code = 'Q09' AND text = 'Quando minha jornada de trabalho se estende, qual é o principal motivo?') OR
    (code = 'Q13' AND text = 'Minha liderança compartilha informações importantes e mudanças que impactam meu trabalho.') OR
    (code = 'Q23' AND text = 'Sinto segurança para realizar um relato ou denúncia sem medo de sofrer retaliação ou consequências negativas.') OR
    (code = 'Q24' AND text = 'Percebo que minha liderança atua de forma ética e coerente com as regras da empresa.') OR
    (code = 'Q30' AND text = 'Consigo manter um equilíbrio adequado entre minha vida profissional e pessoal.')
);
SELECT COUNT(*) INTO @archived_q33_count
FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q33' AND question_number = 0;
SELECT COUNT(*) INTO @reserved_temporary_numbers
FROM survey_questions WHERE survey_id = @survey_id AND question_number BETWEEN 1016 AND 1024;
SELECT COUNT(*) INTO @leadership_section_count
FROM survey_sections WHERE survey_id = @survey_id AND code = 'LIDERANCA';
SELECT question.id AS q24_question_id, question.code AS q24_stable_code,
       COUNT(answer.id) AS q24_historical_answer_count
FROM survey_questions AS question
LEFT JOIN response_answers AS answer
  ON answer.question_id = question.id AND answer.survey_id = question.survey_id
WHERE question.survey_id = @survey_id AND question.code = 'Q24'
GROUP BY question.id, question.code;
SELECT question.id AS question_id, question.code AS stable_code,
       question.question_number, COUNT(answer.id) AS historical_answer_count
FROM survey_questions AS question
LEFT JOIN response_answers AS answer
  ON answer.question_id = question.id AND answer.survey_id = question.survey_id
WHERE question.survey_id = @survey_id
  AND question.code IN ('Q07','Q08','Q09','Q13','Q24','Q30')
GROUP BY question.id, question.code, question.question_number
ORDER BY question.code;
SELECT COUNT(*) INTO @changed_prompt_answer_count
FROM response_answers AS answer
JOIN survey_questions AS question
  ON question.id = answer.question_id AND question.survey_id = answer.survey_id
WHERE question.survey_id = @survey_id
  AND question.code IN ('Q07','Q08','Q09','Q13','Q30');
SELECT COUNT(*) INTO @source_answer_count
FROM response_answers AS answer
JOIN survey_questions AS question
  ON question.id = answer.question_id AND question.survey_id = answer.survey_id
WHERE question.survey_id = @survey_id
  AND question.code IN ('Q16','Q17','Q18','Q19','Q20','Q21','Q22','Q23','Q24');

SET @preflight_ok = IF(
    @survey_id IS NOT NULL AND @leadership_section_id IS NOT NULL
    AND @active_question_count = 41 AND @expected_active_sequence_count = 41
    AND @survey_section_count = 13 AND @q03_profile_count = 1 AND @q32_unified_count = 1
    AND @affected_question_count = 9 AND @expected_old_layout_count = 9
    AND @expected_old_text_count = 7
    AND @archived_q33_count = 1 AND @reserved_temporary_numbers = 0
    AND @leadership_section_count = 1
    AND @approve_historical_prompt_reclassification = 1,
    1, 0
);
SELECT @preflight_ok AS preflight_ready, @survey_id AS survey_id,
       @leadership_section_id AS leadership_section_id,
       @active_question_count AS active_questions_expected_41,
       @expected_active_sequence_count AS existing_numbers_1_to_41_expected_41,
       @survey_section_count AS sections_expected_13,
       @q03_profile_count AS preserved_q03_profile_expected_1,
       @q32_unified_count AS preserved_q32_unified_expected_1,
       @affected_question_count AS stable_codes_q16_to_q24_expected_9,
       @expected_old_layout_count AS prior_positions_expected_9,
       @expected_old_text_count AS prior_texts_expected_7,
       @archived_q33_count AS archived_q33_expected_1,
       @reserved_temporary_numbers AS reserved_temp_numbers_expected_0,
       @source_answer_count AS historical_answers_for_q16_to_q24,
       @changed_prompt_answer_count AS historical_answers_on_reworded_questions,
       @approve_historical_prompt_reclassification AS approval_flag_expected_1_to_proceed;

-- If preflight_ready is not 1, stop and ROLLBACK. These guarded updates will not run.
-- Temporary numbers avoid collisions with UNIQUE(survey_id, question_number).
UPDATE survey_questions
SET question_number = question_number + 1000
WHERE survey_id = @survey_id
  AND code IN ('Q16','Q17','Q18','Q19','Q20','Q21','Q22','Q23','Q24')
  AND @preflight_ok = 1;
SET @shifted_rows = ROW_COUNT();

-- Keep all stable codes; move Q24 and update only the five approved texts.
UPDATE survey_questions
SET
    question_number = CASE code
        WHEN 'Q16' THEN 17 WHEN 'Q17' THEN 18 WHEN 'Q18' THEN 19
        WHEN 'Q19' THEN 20 WHEN 'Q20' THEN 21 WHEN 'Q21' THEN 22
        WHEN 'Q22' THEN 23 WHEN 'Q23' THEN 24 WHEN 'Q24' THEN 16
        ELSE question_number
    END,
    section_id = CASE WHEN code = 'Q24' THEN @leadership_section_id ELSE section_id END,
    position = CASE WHEN code = 'Q24' THEN 6 ELSE position END,
    text = CASE code
        WHEN 'Q07' THEN 'Consigo realizar minhas atividades dentro da minha jornada normal de trabalho.'
        WHEN 'Q08' THEN 'Nos últimos meses, com que frequência você trabalhou além de sua carga horária regular?'
        WHEN 'Q09' THEN 'Quando você trabalha além do seu horário regular, na sua visão, qual costuma ser o principal motivo?'
        WHEN 'Q13' THEN 'Minha liderança compartilha decisões e temas que afetam minhas atividades?'
        WHEN 'Q30' THEN 'As pessoas são encorajadas a equilibrar sua vida profissional e pessoal.'
        ELSE text
    END
WHERE survey_id = @survey_id AND @preflight_ok = 1 AND @shifted_rows = 9
  AND code IN ('Q07','Q08','Q09','Q13','Q16','Q17','Q18','Q19','Q20','Q21','Q22','Q23','Q24','Q30');
SET @updated_rows = ROW_COUNT();

-- Verify active 1..41 ordering and inspect every changed question.
SELECT question.id AS question_id, question.code AS question_code,
       question.question_number, section.code AS section_code, question.position,
       question.analysis_role, question.text
FROM survey_questions AS question
JOIN survey_sections AS section
  ON section.id = question.section_id AND section.survey_id = question.survey_id
WHERE question.survey_id = @survey_id
  AND (question.question_number > 0 OR question.code = 'Q33')
ORDER BY question.question_number, question.code;
SELECT COUNT(*) AS active_question_count, MIN(question_number) AS first_number,
       MAX(question_number) AS last_number, COUNT(DISTINCT question_number) AS distinct_numbers
FROM survey_questions WHERE survey_id = @survey_id AND question_number > 0;
SELECT COUNT(*) INTO @final_answer_count
FROM response_answers AS answer
JOIN survey_questions AS question
  ON question.id = answer.question_id AND question.survey_id = answer.survey_id
WHERE question.survey_id = @survey_id
  AND question.code IN ('Q16','Q17','Q18','Q19','Q20','Q21','Q22','Q23','Q24');
SELECT @updated_rows AS metadata_rows_updated_expected_14,
       @source_answer_count AS historical_answer_count_before,
       @final_answer_count AS historical_answer_count_after,
       (@source_answer_count = @final_answer_count) AS historical_answer_rows_preserved;
SELECT code, question_number, question_type, analysis_role, text
FROM survey_questions
WHERE survey_id = @survey_id
  AND code IN ('Q07','Q08','Q09','Q13','Q16','Q17','Q18','Q19','Q20','Q21','Q22','Q23','Q24','Q30')
ORDER BY question_number;
SELECT code, question_number, text FROM survey_questions
WHERE survey_id = @survey_id AND code IN ('Q03','Q32','Q33') ORDER BY code;

-- Review every postflight result. If anything is unexpected, issue ROLLBACK.
-- Persist only after explicit approval by issuing COMMIT manually in this same session.
