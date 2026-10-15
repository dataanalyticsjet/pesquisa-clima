-- Manual production update for the display title of CLIMATE_2026 only.
-- This changes surveys.title only. It does not modify questions, responses, participation, or history.
-- Review the current title and status before enabling the approval flag.
-- Leave the flag at 0 during review; set it to 1 manually only after approval.
-- No executable COMMIT is included. Inspect the result, then COMMIT or ROLLBACK manually.

START TRANSACTION;

SET @survey_id = (SELECT id FROM surveys WHERE code = 'CLIMATE_2026');
SET @approve_survey_title_update = 0;

SELECT id, code, title, status, version
FROM surveys
WHERE code = 'CLIMATE_2026';

UPDATE surveys
SET title = 'Pesquisa de Engajamento - Voz do Colaborador'
WHERE id = @survey_id
  AND code = 'CLIMATE_2026'
  AND title = 'Pesquisa de Clima Organizacional 2026'
  AND @approve_survey_title_update = 1;
SET @updated_rows = ROW_COUNT();

SELECT id, code, title, status, version, @updated_rows AS title_rows_updated,
       @approve_survey_title_update AS approval_flag
FROM surveys
WHERE code = 'CLIMATE_2026';

-- If the existing title, row count, or output is unexpected, issue ROLLBACK.
-- After review and explicit approval, issue COMMIT manually in this same session.
