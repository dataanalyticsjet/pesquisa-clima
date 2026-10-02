from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_auth_code import ExternalAuthCode


def get_latest_for_email(session: Session, email: str, *, for_update: bool = False) -> ExternalAuthCode | None:
    statement = (
        select(ExternalAuthCode)
        .where(ExternalAuthCode.email == email)
        .order_by(ExternalAuthCode.created_at.desc(), ExternalAuthCode.id.desc())
        .limit(1)
    )
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def add(session: Session, auth_code: ExternalAuthCode) -> ExternalAuthCode:
    session.add(auth_code)
    session.flush()
    return auth_code


def add_failed_attempt(session: Session, auth_code: ExternalAuthCode) -> None:
    auth_code.attempt_count += 1
    session.add(auth_code)
    session.commit()


def consume(session: Session, auth_code: ExternalAuthCode, now: datetime) -> None:
    auth_code.used_at = now
    session.add(auth_code)
