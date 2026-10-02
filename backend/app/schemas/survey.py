from pydantic import BaseModel, ConfigDict


class SurveyOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    label: str
    position: int
    score_value: int | None
    is_exclusive: bool


class SurveyQuestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_number: int
    code: str
    question_type: str
    text: str
    helper_text: str | None
    placeholder: str | None
    low_label: str | None
    high_label: str | None
    required: bool
    position: int
    analysis_role: str
    option_source: str
    options: list[SurveyOptionResponse]


class SurveySectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    position: int
    analysis_type: str
    questions: list[SurveyQuestionResponse]


class SurveyDefinitionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    intro_text: str | None
    completion_text: str | None
    status: str
    version: int
    sections: list[SurveySectionResponse]
