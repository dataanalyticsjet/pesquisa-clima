-- Manual review only. Do not run automatically from application startup or migrations.
-- No database is selected here; there is intentionally no USE or CREATE DATABASE statement.
-- All backend DATETIME values are to be written and interpreted in UTC.
--
-- Privacy boundary:
-- survey_participation belongs to the identity/participation domain.
-- anonymous_responses and its child tables belong to the anonymous response domain.
-- There is deliberately no foreign key or shared identifier between these domains.

CREATE TABLE IF NOT EXISTS surveys (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    title VARCHAR(255) NOT NULL,
    intro_text TEXT NULL,
    completion_text TEXT NULL,
    status ENUM('DRAFT', 'ACTIVE', 'CLOSED') NOT NULL DEFAULT 'DRAFT',
    version INT UNSIGNED NOT NULL DEFAULT 1,
    starts_on DATE NULL,
    ends_on DATE NULL,
    min_group_size INT UNSIGNED NOT NULL DEFAULT 5,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_surveys_code (code)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS survey_sections (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    survey_id BIGINT UNSIGNED NOT NULL,
    code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    title VARCHAR(255) NOT NULL,
    position SMALLINT UNSIGNED NOT NULL,
    analysis_type VARCHAR(16) NOT NULL COMMENT 'SEGMENT, SCORE, MIXED, NPS, or OPEN_TEXT',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_survey_sections_survey_position (survey_id, position),
    UNIQUE KEY uq_survey_sections_survey_code (survey_id, code),
    UNIQUE KEY uq_survey_sections_survey_id_id (survey_id, id),
    CONSTRAINT fk_survey_sections_survey
        FOREIGN KEY (survey_id) REFERENCES surveys (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS survey_questions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    survey_id BIGINT UNSIGNED NOT NULL,
    section_id BIGINT UNSIGNED NOT NULL,
    question_number SMALLINT UNSIGNED NOT NULL,
    code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    question_type ENUM('SELECT', 'SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'LIKERT', 'NPS', 'TEXTAREA', 'SHORT_TEXT') NOT NULL,
    text TEXT NOT NULL,
    helper_text TEXT NULL,
    placeholder VARCHAR(255) NULL,
    low_label VARCHAR(100) NULL,
    high_label VARCHAR(100) NULL,
    required TINYINT(1) NOT NULL DEFAULT 1,
    position SMALLINT UNSIGNED NOT NULL,
    analysis_role ENUM('SEGMENT', 'SCORE', 'CATEGORY', 'NPS', 'OPEN_TEXT') NOT NULL,
    option_source ENUM('STATIC', 'ORG_REGIONAL', 'ORG_BASE', 'ORG_CNPJ') NOT NULL DEFAULT 'STATIC',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_survey_questions_survey_number (survey_id, question_number),
    UNIQUE KEY uq_survey_questions_survey_code (survey_id, code),
    UNIQUE KEY uq_survey_questions_survey_id_id (survey_id, id),
    KEY ix_survey_questions_section_position (section_id, position),
    CONSTRAINT fk_survey_questions_survey
        FOREIGN KEY (survey_id) REFERENCES surveys (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_survey_questions_section_survey
        FOREIGN KEY (survey_id, section_id) REFERENCES survey_sections (survey_id, id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS survey_question_options (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    question_id BIGINT UNSIGNED NOT NULL,
    code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    label VARCHAR(500) NOT NULL,
    position SMALLINT UNSIGNED NOT NULL,
    score_value TINYINT UNSIGNED NULL,
    is_exclusive TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_survey_question_options_question_position (question_id, position),
    UNIQUE KEY uq_survey_question_options_question_code (question_id, code),
    UNIQUE KEY uq_survey_question_options_question_id_id (question_id, id),
    CONSTRAINT fk_survey_question_options_question
        FOREIGN KEY (question_id) REFERENCES survey_questions (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Identity/participation domain: this records only that a user completed a survey.
-- A row represents a completed submission; drafts are not persisted in this schema version.
CREATE TABLE IF NOT EXISTS survey_participation (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    survey_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    status ENUM('COMPLETED') NOT NULL DEFAULT 'COMPLETED',
    completed_on DATE NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_survey_participation_survey_user (survey_id, user_id),
    KEY ix_survey_participation_user_id (user_id),
    CONSTRAINT fk_survey_participation_survey
        FOREIGN KEY (survey_id) REFERENCES surveys (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_survey_participation_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Anonymous response domain: intentionally no user, participation, session, IP, or timestamp.
CREATE TABLE IF NOT EXISTS anonymous_responses (
    response_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    survey_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (response_id),
    UNIQUE KEY uq_anonymous_responses_response_survey (response_id, survey_id),
    KEY ix_anonymous_responses_survey_id (survey_id),
    CONSTRAINT fk_anonymous_responses_survey
        FOREIGN KEY (survey_id) REFERENCES surveys (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS response_answers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    response_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    survey_id BIGINT UNSIGNED NOT NULL,
    question_id BIGINT UNSIGNED NOT NULL,
    text_value TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_response_answers_response_question (response_id, question_id),
    UNIQUE KEY uq_response_answers_id_question (id, question_id),
    KEY ix_response_answers_response_survey (response_id, survey_id),
    KEY ix_response_answers_survey_question (survey_id, question_id),
    CONSTRAINT fk_response_answers_response_survey
        FOREIGN KEY (response_id, survey_id) REFERENCES anonymous_responses (response_id, survey_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_response_answers_survey_question
        FOREIGN KEY (survey_id, question_id) REFERENCES survey_questions (survey_id, id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS response_answer_options (
    answer_id BIGINT UNSIGNED NOT NULL,
    question_id BIGINT UNSIGNED NOT NULL,
    option_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (answer_id, option_id),
    KEY ix_response_answer_options_answer_question (answer_id, question_id),
    KEY ix_response_answer_options_question_option (question_id, option_id),
    CONSTRAINT fk_response_answer_options_answer_question
        FOREIGN KEY (answer_id, question_id) REFERENCES response_answers (id, question_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_response_answer_options_question_option
        FOREIGN KEY (question_id, option_id) REFERENCES survey_question_options (question_id, id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS anonymous_response_segments (
    response_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    segment_type ENUM('REGIONAL', 'AREA', 'BASE', 'CNPJ') NOT NULL,
    segment_code VARCHAR(191) NOT NULL,
    PRIMARY KEY (response_id, segment_type),
    KEY ix_anonymous_response_segments_filter (segment_type, segment_code, response_id),
    CONSTRAINT fk_anonymous_response_segments_response
        FOREIGN KEY (response_id) REFERENCES anonymous_responses (response_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Populate REGIONAL and BASE from the validated official answers to Q1 and Q2.
-- Q3 is a work-profile category and does not create an organizational segment.
-- The CNPJ segment enum value remains only for compatibility with historical response data.
-- AREA source will be defined before backend implementation.
-- Do not infer or populate AREA until the official source is approved.
