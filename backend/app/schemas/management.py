from pydantic import BaseModel, ConfigDict


class ManagementSurveyOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    survey_code: str
    survey_status: str
    min_group_size: int
    completed_participations: int
    anonymous_response_count: int
    respondent_count: int
    analytics_available: bool
    nps: float | None
    invited_count: int | None
    adherence_percent: float | None
    invited_population_source_configured: bool


class ManagementPillarResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    question_count: int
    respondent_count: int
    analytics_available: bool
    index: float | None


class ManagementSurveyPillarsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    survey_code: str
    survey_status: str
    min_group_size: int
    pillars: list[ManagementPillarResponse]


class ManagementAttentionQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_code: str
    question_text: str
    analytics_available: bool
    attention_rate: float | None
    respondent_count: int | None


class ManagementAttentionSC(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sc_code: str
    sc_name: str
    display_name: str
    attention_rate: float | None
    analytics_available: bool
    respondent_count: int | None
    questions: list[ManagementAttentionQuestion]


class ManagementAttentionRegional(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regional_code: str
    attention_rate: float | None
    analytics_available: bool
    respondent_count: int | None
    questions: list[ManagementAttentionQuestion]
    scs: list[ManagementAttentionSC]


class ManagementSurveyAttentionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    survey_code: str
    survey_status: str
    min_group_size: int
    regionals: list[ManagementAttentionRegional]


class ManagementVoiceQuestionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_code: str
    question_text: str
    question_type: str
    analytics_available: bool
    respondent_count: int | None


class ManagementVoiceCommentsQuestion(ManagementVoiceQuestionBase):
    comments: list[str]


class ManagementVoiceTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str
    count: int


class ManagementVoiceTermsQuestion(ManagementVoiceQuestionBase):
    terms: list[ManagementVoiceTerm]


class ManagementSurveyVoiceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    survey_code: str
    survey_status: str
    min_group_size: int
    questions: list[ManagementVoiceCommentsQuestion | ManagementVoiceTermsQuestion]
