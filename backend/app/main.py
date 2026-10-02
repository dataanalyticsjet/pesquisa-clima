from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
import secrets

from app.api.auth import router as auth_router
from app.api.database import router as database_router
from app.api.health import router as health_router
from app.api.management import router as management_router
from app.api.organization import router as organization_router
from app.api.surveys import router as surveys_router
from app.core.config import settings


session_secret = settings.session_secret
if session_secret and len(session_secret.encode("utf-8")) < 32:
    raise RuntimeError("SESSION_SECRET must contain at least 32 bytes")
if not session_secret:
    if settings.app_env.lower() not in {"development", "dev", "local"}:
        raise RuntimeError("SESSION_SECRET must be configured outside local development")
    session_secret = secrets.token_urlsafe(48)
settings.session_secret = session_secret

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)
@app.middleware("http")
async def redact_oauth_callback_query(request, call_next):
    try:
        return await call_next(request)
    finally:
        if request.url.path == "/api/auth/feishu/callback":
            request.scope["query_string"] = b""


app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.session_secure or settings.app_env.lower() in {"production", "prod"},
)

app.include_router(health_router)
app.include_router(database_router)
app.include_router(surveys_router)
app.include_router(management_router)
app.include_router(organization_router)
app.include_router(auth_router)
