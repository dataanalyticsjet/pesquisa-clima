-- Manual review only. This file is not executed by application startup or migrations.
-- Select the officially approved database in the SQL client before a human applies this file.
-- No database name is assumed here and there is intentionally no USE statement.
-- This script creates identity/access tables only; survey response tables are out of scope.
-- All backend DATETIME values are to be written and interpreted in UTC.

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(254) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL,
    name VARCHAR(255) NOT NULL,
    access_type ENUM('INTERNAL', 'EXTERNAL') NOT NULL,
    feishu_open_id VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NULL,
    feishu_union_id VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NULL,
    status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'INACTIVE',
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email),
    UNIQUE KEY uq_users_feishu_open_id (feishu_open_id),
    UNIQUE KEY uq_users_feishu_union_id (feishu_union_id),
    KEY ix_users_status_access_type (status, access_type)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS roles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_roles_code (code)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_roles_user_role (user_id, role_id),
    KEY ix_user_roles_role_id (role_id),
    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role
        FOREIGN KEY (role_id) REFERENCES roles (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS external_auth_codes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(254) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL,
    code_hash VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    attempt_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_external_auth_codes_email_expires_at (email, expires_at),
    KEY ix_external_auth_codes_used_at (used_at)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed only role definitions. This is safe to re-run and creates no users or assignments.
INSERT IGNORE INTO roles (code, name)
VALUES
    ('COLLABORATOR', 'Colaborador'),
    ('MANAGEMENT', 'Gestão'),
    ('SURVEY_ADMIN', 'Administrador de Pesquisas'),
    ('ADMIN', 'Administrador');
