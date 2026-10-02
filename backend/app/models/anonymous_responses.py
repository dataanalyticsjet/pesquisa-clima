from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import BIGINT, CHAR, ENUM, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnonymousResponse(Base):
    __tablename__ = "anonymous_responses"
    __table_args__ = (
        UniqueConstraint(
            "response_id", "survey_id", name="uq_anonymous_responses_response_survey"
        ),
        Index("ix_anonymous_responses_survey_id", "survey_id"),
    )

    response_id: Mapped[str] = mapped_column(
        CHAR(36, charset="ascii", collation="ascii_bin"), primary_key=True
    )
    survey_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("surveys.id", name="fk_anonymous_responses_survey", ondelete="RESTRICT"),
        nullable=False,
    )


class ResponseAnswer(Base):
    __tablename__ = "response_answers"
    __table_args__ = (
        UniqueConstraint("response_id", "question_id", name="uq_response_answers_response_question"),
        UniqueConstraint("id", "question_id", name="uq_response_answers_id_question"),
        Index("ix_response_answers_response_survey", "response_id", "survey_id"),
        Index("ix_response_answers_survey_question", "survey_id", "question_id"),
        ForeignKeyConstraint(
            ["response_id", "survey_id"],
            ["anonymous_responses.response_id", "anonymous_responses.survey_id"],
            name="fk_response_answers_response_survey",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["survey_id", "question_id"],
            ["survey_questions.survey_id", "survey_questions.id"],
            name="fk_response_answers_survey_question",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    response_id: Mapped[str] = mapped_column(
        CHAR(36, charset="ascii", collation="ascii_bin"), nullable=False
    )
    survey_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    question_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResponseAnswerOption(Base):
    __tablename__ = "response_answer_options"
    __table_args__ = (
        Index("ix_response_answer_options_answer_question", "answer_id", "question_id"),
        Index("ix_response_answer_options_question_option", "question_id", "option_id"),
        ForeignKeyConstraint(
            ["answer_id", "question_id"],
            ["response_answers.id", "response_answers.question_id"],
            name="fk_response_answer_options_answer_question",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["question_id", "option_id"],
            ["survey_question_options.question_id", "survey_question_options.id"],
            name="fk_response_answer_options_question_option",
            ondelete="RESTRICT",
        ),
    )

    answer_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    question_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    option_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)


class AnonymousResponseSegment(Base):
    __tablename__ = "anonymous_response_segments"
    __table_args__ = (
        Index(
            "ix_anonymous_response_segments_filter",
            "segment_type",
            "segment_code",
            "response_id",
        ),
        ForeignKeyConstraint(
            ["response_id"],
            ["anonymous_responses.response_id"],
            name="fk_anonymous_response_segments_response",
            ondelete="CASCADE",
        ),
    )

    response_id: Mapped[str] = mapped_column(
        CHAR(36, charset="ascii", collation="ascii_bin"), primary_key=True
    )
    segment_type: Mapped[str] = mapped_column(
        ENUM("REGIONAL", "AREA", "BASE", "CNPJ"), primary_key=True
    )
    segment_code: Mapped[str] = mapped_column(VARCHAR(191), nullable=False)
