from typing import Annotated

from fastapi import Path


SurveyCodePath = Annotated[
    str,
    Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
]
RegionalCodePath = Annotated[str, Path(min_length=1, max_length=64)]
