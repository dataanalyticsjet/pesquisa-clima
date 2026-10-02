from fastapi import FastAPI

from app.api.database import router as database_router
from app.api.health import router as health_router
from app.api.surveys import router as surveys_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)


app.include_router(health_router)
app.include_router(database_router)
app.include_router(surveys_router)
