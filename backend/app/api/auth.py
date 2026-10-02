import secrets
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_db_session
from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.identity_repository import get_user_roles
from app.schemas.auth import AuthMeResponse, LogoutResponse
from app.services.feishu_oauth import FeishuOAuthClient, FeishuTokenExchangeError, FeishuUserInfoError
from app.services.identity_service import AuthFlowError, provision_internal_user


router = APIRouter(prefix="/api/auth", tags=["authentication"])
STATE_SESSION_KEY = "feishu_oauth_state"
STATE_ISSUED_SESSION_KEY = "feishu_oauth_state_issued_at"
STATE_TTL_SECONDS = 600


def _configured_for_oauth() -> bool:
    return bool(
        settings.feishu_oauth_enabled
        and settings.feishu_oauth_app_id
        and settings.feishu_oauth_app_secret
        and settings.feishu_oauth_redirect_uri
    )


def _frontend_redirect(*, auth_error: str | None = None) -> RedirectResponse:
    base = settings.frontend_base_url or "/"
    if auth_error is None:
        return RedirectResponse(base, status_code=303)
    parts = urlsplit(base)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["auth_error"] = auth_error
    return RedirectResponse(
        urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)),
        status_code=303,
    )


@router.get("/feishu/login")
def feishu_login(request: Request):
    if not _configured_for_oauth():
        return _frontend_redirect(auth_error="feishu_disabled")

    state = secrets.token_urlsafe(32)
    request.session[STATE_SESSION_KEY] = state
    request.session[STATE_ISSUED_SESSION_KEY] = int(time.time())
    authorize_params = urlencode(
        {
            "client_id": settings.feishu_oauth_app_id,
            "response_type": "code",
            "redirect_uri": settings.feishu_oauth_redirect_uri,
            "state": state,
        }
    )
    separator = "&" if "?" in settings.feishu_oauth_authorize_url else "?"
    return RedirectResponse(f"{settings.feishu_oauth_authorize_url}{separator}{authorize_params}", status_code=302)


@router.get("/feishu/callback")
def feishu_callback(request: Request, code: str | None = None, state: str | None = None):
    if not _configured_for_oauth():
        return _frontend_redirect(auth_error="feishu_disabled")

    expected_state = request.session.pop(STATE_SESSION_KEY, None)
    issued_at = request.session.pop(STATE_ISSUED_SESSION_KEY, None)
    if not isinstance(state, str) or not isinstance(expected_state, str) or not secrets.compare_digest(state, expected_state):
        return _frontend_redirect(auth_error="invalid_state")
    current_time = int(time.time())
    if not isinstance(issued_at, int) or current_time - issued_at > STATE_TTL_SECONDS or issued_at > current_time:
        return _frontend_redirect(auth_error="expired_state")
    if not isinstance(code, str) or not code.strip():
        return _frontend_redirect(auth_error="missing_code")

    oauth_client = FeishuOAuthClient(
        token_url=settings.feishu_oauth_token_url,
        userinfo_url=settings.feishu_oauth_userinfo_url,
        app_id=settings.feishu_oauth_app_id,
        app_secret=settings.feishu_oauth_app_secret,
    )
    try:
        identity = oauth_client.get_identity(code.strip(), settings.feishu_oauth_redirect_uri)
    except FeishuTokenExchangeError:
        return _frontend_redirect(auth_error="token_exchange_failed")
    except FeishuUserInfoError:
        return _frontend_redirect(auth_error="userinfo_failed")
    except Exception:
        return _frontend_redirect(auth_error="token_exchange_failed")

    db = None
    try:
        db = SessionLocal()
        with db.begin():
            user = provision_internal_user(db, identity)
            user_id = user.id
    except AuthFlowError as error:
        return _frontend_redirect(auth_error=error.code)
    except Exception:
        return _frontend_redirect(auth_error="session_creation_failed")
    finally:
        if db is not None:
            db.close()

    request.session.clear()
    request.session["user_id"] = user_id
    return _frontend_redirect()


@router.get("/me", response_model=AuthMeResponse)
def read_current_user(
    user=Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    roles = get_user_roles(session, user.id)
    return {
        "authenticated": True,
        "user": {
            "name": user.name,
            "email": user.email,
            "access_type": user.access_type,
            "roles": roles,
        },
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request):
    request.session.clear()
    return {"authenticated": False}
