from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExternalAuthCode(Base):
    __tablename__ = "external_auth_codes"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(VARCHAR(254, charset="ascii", collation="ascii_general_ci"), nullable=False)
    code_hash: Mapped[str] = mapped_column(VARCHAR(255, charset="ascii", collation="ascii_bin"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attempt_count: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
