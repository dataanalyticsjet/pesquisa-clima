from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text as sql_text,
)
from sqlalchemy.dialects.mysql import BIGINT, ENUM, INTEGER, SMALLINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Survey(Base):
    __tablename__ = "surveys"
    __table_args__ = (UniqueConstraint("code", name="uq_surveys_code"),)

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    intro_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(ENUM("DRAFT", "ACTIVE", "CLOSED"), nullable=False, server_default="DRAFT")
    version: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, server_default=sql_text("1"))
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    ends_on: Mapped[object | None] = mapped_column(Date, nullable=True)
    min_group_size: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, server_default=sql_text("5"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class SurveySection(Base):
    __tablename__ = "survey_sections"
    __table_args__ = (
        UniqueConstraint("survey_id", "position", name="uq_survey_sections_survey_position"),
        UniqueConstraint("survey_id", "code", name="uq_survey_sections_survey_code"),
        UniqueConstraint("survey_id", "id", name="uq_survey_sections_survey_id_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    survey_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"
    __table_args__ = (
        UniqueConstraint("survey_id", "question_number", name="uq_survey_questions_survey_number"),
        UniqueConstraint("survey_id", "code", name="uq_survey_questions_survey_code"),
        UniqueConstraint("survey_id", "id", name="uq_survey_questions_survey_id_id"),
        Index("ix_survey_questions_section_position", "section_id", "position"),
        ForeignKeyConstraint(
            ["survey_id", "section_id"],
            ["survey_sections.survey_id", "survey_sections.id"],
            name="fk_survey_questions_section_survey",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    survey_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    question_number: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    question_type: Mapped[str] = mapped_column(ENUM("SELECT", "SINGLE_CHOICE", "MULTIPLE_CHOICE", "LIKERT", "NPS", "TEXTAREA", "SHORT_TEXT"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    helper_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    low_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    high_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("1"))
    position: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    analysis_role: Mapped[str] = mapped_column(ENUM("SEGMENT", "SCORE", "CATEGORY", "NPS", "OPEN_TEXT"), nullable=False)
    option_source: Mapped[str] = mapped_column(ENUM("STATIC", "ORG_REGIONAL", "ORG_BASE", "ORG_CNPJ"), nullable=False, server_default="STATIC")
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class SurveyQuestionOption(Base):
    __tablename__ = "survey_question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "position", name="uq_survey_question_options_question_position"),
        UniqueConstraint("question_id", "code", name="uq_survey_question_options_question_code"),
        UniqueConstraint("question_id", "id", name="uq_survey_question_options_question_id_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("survey_questions.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    score_value: Mapped[int | None] = mapped_column(TINYINT(unsigned=True), nullable=True)
    is_exclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("0"))
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
