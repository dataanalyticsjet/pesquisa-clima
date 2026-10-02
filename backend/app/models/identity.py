from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT, ENUM, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("feishu_open_id", name="uq_users_feishu_open_id"),
        UniqueConstraint("feishu_union_id", name="uq_users_feishu_union_id"),
        Index("ix_users_status_access_type", "status", "access_type"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(VARCHAR(254, charset="ascii", collation="ascii_general_ci"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_type: Mapped[str] = mapped_column(ENUM("INTERNAL", "EXTERNAL"), nullable=False)
    feishu_open_id: Mapped[str | None] = mapped_column(VARCHAR(255, charset="ascii", collation="ascii_bin"), nullable=True)
    feishu_union_id: Mapped[str | None] = mapped_column(VARCHAR(255, charset="ascii", collation="ascii_bin"), nullable=True)
    status: Mapped[str] = mapped_column(ENUM("ACTIVE", "INACTIVE"), nullable=False, server_default="INACTIVE")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(VARCHAR(32, charset="ascii", collation="ascii_bin"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", name="fk_user_roles_user", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("roles.id", name="fk_user_roles_role", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
