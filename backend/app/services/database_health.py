from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal


class DatabaseNotConfiguredError(Exception):
    pass


class SurveyNotFoundError(Exception):
    pass


def read_database_health() -> dict[str, object]:
    if not all((settings.db_host.strip(), settings.db_name.strip(), settings.db_user.strip(), settings.db_password)):
        raise DatabaseNotConfiguredError

    with SessionLocal() as session:
        session.execute(text("SELECT 1")).scalar_one()
        survey = session.execute(
            text(
                """
                SELECT code, title, status, version, min_group_size
                FROM surveys
                WHERE code = :code
                """
            ),
            {"code": "CLIMATE_2026"},
        ).mappings().one_or_none()

    if survey is None:
        raise SurveyNotFoundError

    return {
        "status": "ok",
        "database": settings.db_name,
        "survey": {
            "code": survey["code"],
            "status": survey["status"],
            "version": survey["version"],
            "min_group_size": survey["min_group_size"],
        },
    }
