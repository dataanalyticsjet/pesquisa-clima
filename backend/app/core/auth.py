from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.identity import User
from app.repositories.identity_repository import get_user_by_id


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="UNAUTHENTICATED")
    user = get_user_by_id(session, user_id)
    if user is None or user.status != "ACTIVE":
        request.session.clear()
        raise HTTPException(status_code=401, detail="UNAUTHENTICATED")
    return user
