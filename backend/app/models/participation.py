from datetime import date

from sqlalchemy import Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SurveyParticipation(Base):
    __tablename__ = "survey_participation"
    __table_args__ = (
        UniqueConstraint("survey_id", "user_id", name="uq_survey_participation_survey_user"),
        Index("ix_survey_participation_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    survey_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("surveys.id", name="fk_survey_participation_survey", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", name="fk_survey_participation_user", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        ENUM("COMPLETED"), nullable=False, server_default="COMPLETED"
    )
    completed_on: Mapped[date] = mapped_column(Date, nullable=False)
