from datetime import date

from pydantic import BaseModel, ConfigDict


class ParticipationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    survey_code: str
    completed: bool
    completed_on: date | None = None
