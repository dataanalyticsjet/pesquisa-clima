-- EXECUÇÃO MANUAL ÚNICA: revisar a saída de conferência antes de confirmar.
-- Não é migration e não é executado pela aplicação.
-- Preserva Q33 e todas as respostas históricas; não há DELETE.
-- Se qualquer saída divergir do esperado, execute ROLLBACK e interrompa.

START TRANSACTION;

SET @survey_id = (
    SELECT id
    FROM surveys
    WHERE code = 'CLIMATE_2026'
    LIMIT 1
);

-- Pré-condição esperada: 42 linhas, códigos Q01..Q42, Q32 em 32 e Q33 em 33.
SELECT q.code, q.question_number, q.position, q.question_type, q.text
FROM survey_questions AS q
WHERE q.survey_id = @survey_id
  AND q.code IN ('Q32', 'Q33', 'Q34', 'Q35', 'Q36', 'Q37', 'Q38', 'Q39', 'Q40', 'Q41', 'Q42')
ORDER BY q.question_number, q.id;

-- Arquiva Q33 sem remover a linha referenciada por respostas históricas.
UPDATE survey_questions
SET question_number = 0,
    position = 0
WHERE survey_id = @survey_id
  AND code = 'Q33'
  AND question_number = 33;

-- Libera os números 33..41 sem colisão com a UNIQUE (survey_id, question_number).
UPDATE survey_questions
SET question_number = question_number + 100
WHERE survey_id = @survey_id
  AND code IN ('Q34', 'Q35', 'Q36', 'Q37', 'Q38', 'Q39', 'Q40', 'Q41', 'Q42')
  AND question_number BETWEEN 34 AND 42;

UPDATE survey_questions
SET question_number = question_number - 101
WHERE survey_id = @survey_id
  AND code IN ('Q34', 'Q35', 'Q36', 'Q37', 'Q38', 'Q39', 'Q40', 'Q41', 'Q42')
  AND question_number BETWEEN 134 AND 142;

-- Atualiza somente o texto oficial de Q32 e a ordem local das perguntas da seção.
UPDATE survey_questions
SET text = 'Os sanitários da unidade são mantidos em condições de higiene, conservados e em bom estado de funcionamento?'
WHERE survey_id = @survey_id
  AND code = 'Q32'
  AND question_number = 32;

UPDATE survey_questions
SET position = 2
WHERE survey_id = @survey_id
  AND code = 'Q34'
  AND question_number = 33;

UPDATE survey_questions
SET position = 3
WHERE survey_id = @survey_id
  AND code = 'Q35'
  AND question_number = 34;

-- Pós-condição esperada: 41 ativas (1..41), Q33 em 0, Q34..Q42 renumeradas.
SELECT COUNT(*) AS active_question_count,
       MIN(question_number) AS first_display_number,
       MAX(question_number) AS last_display_number,
       COUNT(DISTINCT question_number) AS distinct_display_numbers
FROM survey_questions
WHERE survey_id = @survey_id
  AND question_number > 0;

SELECT q.code, q.question_number, q.position, q.question_type, q.text
FROM survey_questions AS q
WHERE q.survey_id = @survey_id
  AND q.code IN ('Q32', 'Q33', 'Q34', 'Q35', 'Q36', 'Q37', 'Q38', 'Q39', 'Q40', 'Q41', 'Q42')
ORDER BY q.question_number, q.id;

-- Confirme que o resultado mostra 41 / 1 / 41 / 41 e que Q33 permanece com número 0.
-- Depois da conferência manual, execute COMMIT; caso contrário, execute ROLLBACK.
