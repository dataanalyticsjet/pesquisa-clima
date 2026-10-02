from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import Role, User, UserRole


def get_user_by_email(session: Session, email: str, *, for_update: bool = False) -> User | None:
    statement = select(User).where(User.email == email)
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def get_users_by_feishu_ids(
    session: Session, open_id: str | None, union_id: str | None
) -> list[User]:
    from sqlalchemy import or_

    checks = []
    if open_id:
        checks.append(User.feishu_open_id == open_id)
    if union_id:
        checks.append(User.feishu_union_id == union_id)
    return list(session.scalars(select(User).where(or_(*checks))).all()) if checks else []


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def get_user_roles(session: Session, user_id: int) -> list[str]:
    statement = select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id).order_by(Role.code)
    return list(session.scalars(statement))


def get_role_by_code(session: Session, code: str) -> Role | None:
    return session.scalar(select(Role).where(Role.code == code))


def add_user(session: Session, *, email: str, name: str, open_id: str | None, union_id: str | None) -> User:
    user = User(
        email=email,
        name=name,
        access_type="INTERNAL",
        status="ACTIVE",
        feishu_open_id=open_id,
        feishu_union_id=union_id,
    )
    session.add(user)
    session.flush()
    return user


def add_external_user(session: Session, *, email: str, name: str = "Usuário externo") -> User:
    user = User(email=email, name=name, access_type="EXTERNAL", status="ACTIVE")
    session.add(user)
    session.flush()
    return user


def add_user_role(session: Session, user_id: int, role_id: int) -> None:
    session.add(UserRole(user_id=user_id, role_id=role_id))
