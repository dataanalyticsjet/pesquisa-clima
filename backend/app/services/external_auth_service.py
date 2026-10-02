import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.external_auth_code import ExternalAuthCode
from app.models.identity import User
from app.repositories import external_auth_repository, identity_repository
from app.services.email_service import EmailService, EmailUnavailableError, email_service


logger = logging.getLogger(__name__)
OTP_PATTERN = re.compile(r"^[0-9]{6}$")
LOCAL_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$")
DOMAIN_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
GENERIC_REQUEST_MESSAGE = "Se o e-mail puder receber acesso, um código será enviado."


class ExternalAuthError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def normalize_external_email(email: str) -> str:
    normalized = email.strip().lower()
    if not normalized.isascii() or len(normalized) > 254 or normalized.count("@") != 1:
        raise ExternalAuthError("invalid_email")
    local, _, domain = normalized.rpartition("@")
    labels = domain.split(".")
    if (
        not local
        or len(local) > 64
        or not LOCAL_EMAIL_PATTERN.fullmatch(local)
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
        or len(labels) < 2
        or any(not DOMAIN_LABEL_PATTERN.fullmatch(label) for label in labels)
    ):
        raise ExternalAuthError("invalid_email")
    return normalized


def _is_corporate_email(email: str) -> bool:
    return email.rpartition("@")[2] in settings.corporate_domain_allowlist


def _code_hash(email: str, code: str) -> str:
    secret = settings.session_secret
    if not secret:
        raise ExternalAuthError("external_auth_unavailable")
    message = f"external:{email}:{code}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def request_external_login_code(
    session: Session,
    email: str,
    *,
    mailer: EmailService | None = None,
) -> bool:
    if not settings.external_email_login_enabled or not settings.session_secret or not settings.smtp_configured:
        raise ExternalAuthError("external_auth_unavailable")
    normalized = normalize_external_email(email)
    if _is_corporate_email(normalized):
        return False

    now = _now_utc()
    try:
        user = identity_repository.get_user_by_email(session, normalized, for_update=True)
        if user is not None and (user.access_type != "EXTERNAL" or user.status != "ACTIVE"):
            return False

        latest = external_auth_repository.get_latest_for_email(session, normalized, for_update=True)
        if latest is not None and (now - latest.created_at).total_seconds() < settings.auth_code_resend_seconds:
            return False

        code = f"{secrets.randbelow(1_000_000):06d}"
        (mailer or email_service).send_login_code(
            normalized, code, settings.auth_code_ttl_minutes
        )
        external_auth_repository.add(
            session,
            ExternalAuthCode(
                email=normalized,
                code_hash=_code_hash(normalized, code),
                expires_at=now + timedelta(minutes=settings.auth_code_ttl_minutes),
                attempt_count=0,
            ),
        )
        session.commit()
    except EmailUnavailableError as error:
        session.rollback()
        logger.error("external_auth.request Email delivery unavailable")
        raise ExternalAuthError("external_auth_unavailable") from error
    except ExternalAuthError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        logger.error("external_auth.request Failed to issue OTP")
        raise ExternalAuthError("external_auth_unavailable") from None

    logger.info("external_auth.request OTP requested and hash persisted")
    return True


def verify_external_login_code(session: Session, email: str, code: str) -> User:
    if not settings.external_email_login_enabled or not settings.session_secret:
        raise ExternalAuthError("external_auth_unavailable")
    normalized = normalize_external_email(email)
    if not OTP_PATTERN.fullmatch(code):
        raise ExternalAuthError("invalid_code")
    if _is_corporate_email(normalized):
        raise ExternalAuthError("identity_conflict")

    now = _now_utc()
    try:
        user = identity_repository.get_user_by_email(session, normalized, for_update=True)
        if user is not None and user.access_type != "EXTERNAL":
            raise ExternalAuthError("identity_conflict")

        auth_code = external_auth_repository.get_latest_for_email(
            session, normalized, for_update=True
        )
        if auth_code is None or auth_code.used_at is not None:
            raise ExternalAuthError("invalid_code")
        if auth_code.expires_at <= now:
            raise ExternalAuthError("expired_code")
        if auth_code.attempt_count >= settings.auth_code_max_attempts:
            raise ExternalAuthError("invalid_code")

        expected = _code_hash(normalized, code)
        if not hmac.compare_digest(auth_code.code_hash, expected):
            external_auth_repository.add_failed_attempt(session, auth_code)
            logger.info("external_auth.verify Invalid OTP")
            raise ExternalAuthError("invalid_code")

        if user is not None and user.status != "ACTIVE":
            external_auth_repository.consume(session, auth_code, now)
            session.commit()
            raise ExternalAuthError("user_inactive")

        if user is None:
            user = identity_repository.add_external_user(session, email=normalized)
            role = identity_repository.get_role_by_code(session, "COLLABORATOR")
            if role is None:
                raise ExternalAuthError("external_auth_unavailable")
            identity_repository.add_user_role(session, user.id, role.id)

        user.last_login_at = now
        external_auth_repository.consume(session, auth_code, now)
        session.commit()
    except ExternalAuthError:
        raise
    except Exception:
        session.rollback()
        logger.error("external_auth.verify Failed to validate OTP")
        raise ExternalAuthError("external_auth_unavailable") from None

    logger.info("external_auth.verify OTP validated")
    return user
