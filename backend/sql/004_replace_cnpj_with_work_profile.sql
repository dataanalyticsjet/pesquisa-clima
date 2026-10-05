-- Manual migration for CLIMATE_2026 only. Review the target IDs before committing.
-- Never execute this migration from application startup or deployment automation.
-- Historical answer rows and CNPJ segments are intentionally preserved.

START TRANSACTION;

SET @survey_id = (SELECT id FROM surveys WHERE code = 'CLIMATE_2026');
SET @q03_id = (SELECT id FROM survey_questions WHERE survey_id = @survey_id AND code = 'Q03');

UPDATE survey_questions
SET question_type = 'SINGLE_CHOICE',
    text = 'Seu perfil de atuação é:',
    helper_text = NULL,
    placeholder = NULL,
    analysis_role = 'CATEGORY',
    option_source = 'STATIC'
WHERE id = @q03_id AND survey_id = @survey_id;

INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
SELECT @q03_id, 'OPERATIONAL', 'Operacional', 1, NULL, 0
WHERE @q03_id IS NOT NULL
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

INSERT INTO survey_question_options (question_id, code, label, position, score_value, is_exclusive)
SELECT @q03_id, 'ADMINISTRATIVE', 'Administrativo', 2, NULL, 0
WHERE @q03_id IS NOT NULL
ON DUPLICATE KEY UPDATE label = VALUES(label), position = VALUES(position), score_value = VALUES(score_value), is_exclusive = VALUES(is_exclusive);

-- Delete only obsolete Q03 options that have no historical answer references.
-- Referenced legacy choices stay stored and are hidden from the active Q03 definition API.
DELETE old_option
FROM survey_question_options AS old_option
WHERE old_option.question_id = @q03_id
  AND old_option.code NOT IN ('OPERATIONAL', 'ADMINISTRATIVE')
  AND NOT EXISTS (
      SELECT 1
      FROM response_answer_options AS answer_option
      WHERE answer_option.question_id = old_option.question_id
        AND answer_option.option_id = old_option.id
  );

-- Review this result before considering the migration complete.
SELECT s.code AS survey_code, q.code AS question_code, q.question_type, q.text,
       q.option_source, o.code AS option_code, o.label, o.position
FROM surveys AS s
JOIN survey_questions AS q ON q.survey_id = s.id AND q.code = 'Q03'
LEFT JOIN survey_question_options AS o ON o.question_id = q.id
WHERE s.id = @survey_id
ORDER BY o.position, o.id;

COMMIT;
