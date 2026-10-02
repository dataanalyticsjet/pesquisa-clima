from pydantic import BaseModel, ConfigDict, Field


class SurveyAnswerSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    option_codes: list[str] | None = Field(default=None, max_length=100)
    text_value: str | None = Field(default=None, max_length=20_000)


class SurveySubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: list[SurveyAnswerSubmission] = Field(max_length=42)


class SurveySubmissionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submitted: bool
