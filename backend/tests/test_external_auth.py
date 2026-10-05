from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core import auth as auth_core
from app.core.config import settings
from app.main import app
from app.models.external_auth_code import ExternalAuthCode
from app.repositories import external_auth_repository, identity_repository
from app.services import external_auth_service
from app.services.email_service import EmailService, EmailUnavailableError


client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def otp_settings(monkeypatch):
    client.cookies.clear()
    client.app.dependency_overrides.clear()
    monkeypatch.setattr(settings, "external_email_login_enabled", True)
    monkeypatch.setattr(settings, "auth_code_ttl_minutes", 10)
    monkeypatch.setattr(settings, "auth_code_max_attempts", 5)
    monkeypatch.setattr(settings, "auth_code_resend_seconds", 60)
    monkeypatch.setattr(settings, "allowed_corporate_domains", "jtexpress.com.br")
    monkeypatch.setattr(settings, "session_secret", "session-secret-test-only-0123456789")
    monkeypatch.setattr(settings, "smtp_host", "smtp.invalid")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")
    monkeypatch.setattr(settings, "smtp_from", "no-reply@example.test")
    monkeypatch.setattr(settings, "smtp_ssl", False)
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_timeout_seconds", 10)
    yield
    client.cookies.clear()
    client.app.dependency_overrides.clear()


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, item):
        self.added.append(item)

    def flush(self):
        return None

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeMailer:
    def __init__(self):
        self.sent = []

    def send_login_code(self, recipient, code, ttl_minutes):
        self.sent.append((recipient, code, ttl_minutes))


def user(*, user_id=17, access_type="EXTERNAL", status="ACTIVE", name="Usuário externo"):
    return SimpleNamespace(
        id=user_id,
        email="third.party@example.com",
        name=name,
        access_type=access_type,
        status=status,
        feishu_open_id="private-open-id",
        feishu_union_id="private-union-id",
        last_login_at=None,
    )


def code_record(otp="123456", *, email="third.party@example.com", expires=None, used=None, attempts=0):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return SimpleNamespace(
        id=31,
        email=email,
        code_hash=external_auth_service._code_hash(email, otp),
        expires_at=expires or now + timedelta(minutes=10),
        used_at=used,
        attempt_count=attempts,
        created_at=now - timedelta(minutes=2),
    )


def setup_request_repositories(monkeypatch, *, current_user=None, latest=None):
    captured = {"codes": [], "role_assignments": [], "new_users": []}
    monkeypatch.setattr(identity_repository, "get_user_by_email", lambda session, email, **kwargs: current_user)
    monkeypatch.setattr(external_auth_repository, "get_latest_for_email", lambda session, email, **kwargs: latest)

    def add_code(session, item):
        captured["codes"].append(item)
        return item

    monkeypatch.setattr(external_auth_repository, "add", add_code)
    return captured


def setup_verify_repositories(monkeypatch, *, current_user=None, latest=None, role=SimpleNamespace(id=4, code="COLLABORATOR")):
    captured = {"new_users": [], "roles": []}
    monkeypatch.setattr(identity_repository, "get_user_by_email", lambda session, email, **kwargs: current_user)
    monkeypatch.setattr(external_auth_repository, "get_latest_for_email", lambda session, email, **kwargs: latest)
    monkeypatch.setattr(identity_repository, "get_role_by_code", lambda session, code: role if code == "COLLABORATOR" else None)

    def add_user(session, *, email, name="Usuário externo"):
        created = user(user_id=72, name=name)
        created.email = email
        captured["new_users"].append(created)
        return created

    monkeypatch.setattr(identity_repository, "add_external_user", add_user)
    monkeypatch.setattr(identity_repository, "add_user_role", lambda session, uid, rid: captured["roles"].append((uid, rid)))
    return captured


def test_request_accepts_valid_external_email_and_sends_code(monkeypatch):
    captured = setup_request_repositories(monkeypatch)
    mailer = FakeMailer()
    assert external_auth_service.request_external_login_code(
        FakeSession(), "third.party@example.com", mailer=mailer
    ) is True
    assert mailer.sent[0][0] == "third.party@example.com"
    assert len(captured["codes"]) == 1


def test_gmail_address_can_request_external_code(monkeypatch):
    captured = setup_request_repositories(monkeypatch)
    mailer = FakeMailer()

    result = external_auth_service.request_external_login_code(
        FakeSession(), "External.Person@Gmail.com", mailer=mailer
    )

    assert result is True
    assert mailer.sent[0][0] == "external.person@gmail.com"
    assert captured["codes"][0].email == "external.person@gmail.com"


def test_request_normalizes_email_before_sending_and_storing(monkeypatch):
    captured = setup_request_repositories(monkeypatch)
    mailer = FakeMailer()
    external_auth_service.request_external_login_code(
        FakeSession(), " Third.Party@Example.COM ", mailer=mailer
    )
    assert mailer.sent[0][0] == "third.party@example.com"
    assert captured["codes"][0].email == "third.party@example.com"


def test_code_is_cryptographically_generated_as_six_digits(monkeypatch):
    setup_request_repositories(monkeypatch)
    mailer = FakeMailer()
    monkeypatch.setattr(external_auth_service.secrets, "randbelow", lambda limit: 7312)
    external_auth_service.request_external_login_code(FakeSession(), "x@example.com", mailer=mailer)
    assert mailer.sent[0][1] == "007312"
    assert len(mailer.sent[0][1]) == 6 and mailer.sent[0][1].isdigit()


def test_only_hmac_hash_is_persisted(monkeypatch):
    captured = setup_request_repositories(monkeypatch)
    mailer = FakeMailer()
    external_auth_service.request_external_login_code(FakeSession(), "x@example.com", mailer=mailer)
    otp = mailer.sent[0][1]
    stored = captured["codes"][0].code_hash
    assert stored != otp
    assert len(stored) == 64
    assert otp not in stored


def test_hash_is_keyed_hmac_and_email_bound():
    first = external_auth_service._code_hash("one@example.com", "123456")
    second = external_auth_service._code_hash("two@example.com", "123456")
    assert first != second and len(first) == 64


def test_request_uses_cooldown_without_invalidating_historical_rows(monkeypatch):
    issued_at = datetime(2026, 10, 5, 15, 8, 48)
    recent = code_record(expires=issued_at + timedelta(minutes=settings.auth_code_ttl_minutes))
    recent.created_at = issued_at + timedelta(hours=8)
    monkeypatch.setattr(external_auth_service, "_now_utc", lambda: issued_at + timedelta(seconds=59))
    captured = setup_request_repositories(monkeypatch, latest=recent)
    mailer = FakeMailer()
    result = external_auth_service.request_external_login_code(FakeSession(), recent.email, mailer=mailer)
    assert result is False and mailer.sent == [] and captured["codes"] == []


def test_request_sends_again_at_cooldown_boundary_despite_mysql_created_at(monkeypatch):
    issued_at = datetime(2026, 10, 5, 15, 8, 48)
    latest = code_record(expires=issued_at + timedelta(minutes=settings.auth_code_ttl_minutes))
    latest.created_at = issued_at + timedelta(hours=8)
    monkeypatch.setattr(external_auth_service, "_now_utc", lambda: issued_at + timedelta(seconds=60))
    captured = setup_request_repositories(monkeypatch, latest=latest)
    mailer = FakeMailer()

    result = external_auth_service.request_external_login_code(
        FakeSession(), latest.email, mailer=mailer
    )

    assert result is True
    assert len(mailer.sent) == 1
    assert len(captured["codes"]) == 1


def test_request_mail_failure_is_generic_and_does_not_log_email_or_code(monkeypatch, caplog):
    setup_request_repositories(monkeypatch)
    monkeypatch.setattr(external_auth_service.secrets, "randbelow", lambda limit: 123456)

    class UnavailableMailer:
        def send_login_code(self, recipient, code, ttl_minutes):
            raise EmailUnavailableError("recipient x@example.com code 123456")

    with pytest.raises(external_auth_service.ExternalAuthError, match="external_auth_unavailable"):
        external_auth_service.request_external_login_code(
            FakeSession(), "x@example.com", mailer=UnavailableMailer()
        )

    assert "x@example.com" not in caplog.text
    assert "123456" not in caplog.text


def test_only_the_latest_code_is_selected_for_validation(monkeypatch):
    older = code_record("111111")
    latest = code_record("222222")
    setup_verify_repositories(monkeypatch, latest=latest)
    with pytest.raises(external_auth_service.ExternalAuthError, match="invalid_code"):
        external_auth_service.verify_external_login_code(FakeSession(), latest.email, "111111")
    verified = external_auth_service.verify_external_login_code(FakeSession(), latest.email, "222222")
    assert verified.access_type == "EXTERNAL"
    assert older.code_hash != latest.code_hash


def test_internal_or_inactive_account_request_is_suppressed_generically(monkeypatch):
    current = user(access_type="INTERNAL")
    setup_request_repositories(monkeypatch, current_user=current)
    mailer = FakeMailer()
    assert external_auth_service.request_external_login_code(FakeSession(), current.email, mailer=mailer) is False
    assert mailer.sent == []


@pytest.mark.parametrize("email", ["", "no-at-sign", "a@localhost", "a@@example.com", "a..b@example.com", "a@example..com"])
def test_invalid_email_rejected(email):
    with pytest.raises(external_auth_service.ExternalAuthError, match="invalid_email"):
        external_auth_service.normalize_external_email(email)


def test_external_email_not_restricted_to_corporate_domain():
    assert external_auth_service.normalize_external_email("Vendor@Another-Company.org") == "vendor@another-company.org"


def test_valid_code_creates_new_external_user_and_only_collaborator(monkeypatch):
    latest = code_record()
    captured = setup_verify_repositories(monkeypatch, latest=latest)
    session = FakeSession()
    created = external_auth_service.verify_external_login_code(session, latest.email, "123456")
    assert created.access_type == "EXTERNAL" and created.status == "ACTIVE"
    assert created.name == "Usuário externo"
    assert captured["roles"] == [(72, 4)]
    assert latest.used_at is not None and session.commits == 1


def test_new_external_user_does_not_receive_privileged_roles(monkeypatch):
    latest = code_record()
    captured = setup_verify_repositories(monkeypatch, latest=latest)
    external_auth_service.verify_external_login_code(FakeSession(), latest.email, "123456")
    assert captured["roles"] == [(72, 4)]


def test_existing_external_user_is_reused_and_roles_untouched(monkeypatch):
    existing = user()
    latest = code_record()
    captured = setup_verify_repositories(monkeypatch, current_user=existing, latest=latest)
    session = FakeSession()
    returned = external_auth_service.verify_external_login_code(session, existing.email, "123456")
    assert returned is existing and existing.last_login_at is not None
    assert captured["new_users"] == [] and captured["roles"] == []
    assert session.commits == 1


def test_inactive_external_account_is_blocked_and_code_consumed(monkeypatch):
    inactive = user(status="INACTIVE")
    latest = code_record()
    setup_verify_repositories(monkeypatch, current_user=inactive, latest=latest)
    session = FakeSession()
    with pytest.raises(external_auth_service.ExternalAuthError, match="user_inactive"):
        external_auth_service.verify_external_login_code(session, inactive.email, "123456")
    assert latest.used_at is not None and session.commits == 1


def test_internal_account_conflict_does_not_change_identity_or_roles(monkeypatch):
    internal = user(access_type="INTERNAL")
    latest = code_record()
    captured = setup_verify_repositories(monkeypatch, current_user=internal, latest=latest)
    with pytest.raises(external_auth_service.ExternalAuthError, match="identity_conflict"):
        external_auth_service.verify_external_login_code(FakeSession(), internal.email, "123456")
    assert internal.access_type == "INTERNAL"
    assert captured["new_users"] == [] and captured["roles"] == []


@pytest.mark.parametrize("otp", ["000000", "999999", "654321"])
def test_incorrect_code_increments_attempts(otp, monkeypatch):
    latest = code_record()
    setup_verify_repositories(monkeypatch, latest=latest)
    session = FakeSession()
    with pytest.raises(external_auth_service.ExternalAuthError, match="invalid_code"):
        external_auth_service.verify_external_login_code(session, latest.email, otp)
    assert latest.attempt_count == 1 and session.commits == 1


def test_expired_code_is_rejected(monkeypatch):
    now = datetime(2026, 10, 5, 15, 8, 48)
    old = now - timedelta(seconds=1)
    latest = code_record(expires=old)
    latest.created_at = now + timedelta(hours=8)
    monkeypatch.setattr(external_auth_service, "_now_utc", lambda: now)
    setup_verify_repositories(monkeypatch, latest=latest)
    with pytest.raises(external_auth_service.ExternalAuthError, match="expired_code"):
        external_auth_service.verify_external_login_code(FakeSession(), latest.email, "123456")


def test_used_code_cannot_be_reused(monkeypatch):
    latest = code_record(used=datetime.now(timezone.utc).replace(tzinfo=None))
    setup_verify_repositories(monkeypatch, latest=latest)
    with pytest.raises(external_auth_service.ExternalAuthError, match="invalid_code"):
        external_auth_service.verify_external_login_code(FakeSession(), latest.email, "123456")


def test_maximum_attempts_blocks_code(monkeypatch):
    latest = code_record(attempts=settings.auth_code_max_attempts)
    setup_verify_repositories(monkeypatch, latest=latest)
    with pytest.raises(external_auth_service.ExternalAuthError, match="invalid_code"):
        external_auth_service.verify_external_login_code(FakeSession(), latest.email, "123456")


def test_corporate_internal_domain_cannot_use_external_otp():
    assert external_auth_service.request_external_login_code(FakeSession(), "someone@jtexpress.com.br", mailer=FakeMailer()) is False
    with pytest.raises(external_auth_service.ExternalAuthError, match="identity_conflict"):
        external_auth_service.verify_external_login_code(FakeSession(), "someone@jtexpress.com.br", "123456")


def test_request_response_is_generic_and_does_not_expose_code(monkeypatch):
    setup_request_repositories(monkeypatch)
    monkeypatch.setattr(auth_api, "request_external_login_code", lambda session, email: True)
    client.app.dependency_overrides.clear()
    response = client.post("/api/auth/external/request-code", json={"email": "x@example.com"})
    assert response.status_code == 200
    assert response.json() == {"message": external_auth_service.GENERIC_REQUEST_MESSAGE}
    assert "123456" not in response.text and "code_hash" not in response.text


def test_request_endpoint_never_reveals_internal_email(monkeypatch):
    monkeypatch.setattr(auth_api, "request_external_login_code", lambda session, email: False)
    response = client.post("/api/auth/external/request-code", json={"email": "internal@jtexpress.com.br"})
    assert response.status_code == 200
    assert response.json() == {"message": external_auth_service.GENERIC_REQUEST_MESSAGE}


def test_verify_endpoint_creates_same_local_session_cookie(monkeypatch):
    current = user()
    monkeypatch.setattr(auth_api, "verify_external_login_code", lambda session, email, code: current)
    from app.core.auth import get_db_session
    client.app.dependency_overrides[get_db_session] = lambda: FakeSession()
    response = client.post("/api/auth/external/verify-code", json={"email": current.email, "code": "123456"})
    assert response.status_code == 200 and response.json() == {"authenticated": True}
    cookie = response.headers["set-cookie"].lower()
    assert settings.session_cookie_name.lower() in cookie and "httponly" in cookie
    assert "123456" not in response.text


def test_me_returns_external_account_without_private_ids(monkeypatch):
    current = user()
    monkeypatch.setattr(auth_core, "get_user_by_id", lambda session, uid: current)
    monkeypatch.setattr(auth_api, "get_user_roles", lambda session, uid: ["COLLABORATOR"])
    monkeypatch.setattr(auth_api, "verify_external_login_code", lambda session, email, code: current)
    from app.core.auth import get_db_session
    client.app.dependency_overrides[get_db_session] = lambda: FakeSession()
    client.post("/api/auth/external/verify-code", json={"email": current.email, "code": "123456"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "user": {"name": current.name, "email": current.email, "access_type": "EXTERNAL", "roles": ["COLLABORATOR"]},
    }
    assert current.feishu_open_id not in response.text and current.feishu_union_id not in response.text


def test_logout_clears_external_session():
    response = client.post("/api/auth/logout")
    assert response.status_code == 200 and response.json() == {"authenticated": False}


def test_email_service_smtp_is_mocked_and_never_sends_real_mail(monkeypatch):
    smtp = Mock()
    smtp.__enter__ = Mock(return_value=smtp)
    smtp.__exit__ = Mock(return_value=False)
    with patch("app.services.email_service.smtplib.SMTP", return_value=smtp) as smtp_class:
        EmailService().send_login_code("user@example.com", "123456", 10)
    smtp_class.assert_called_once()
    smtp.send_message.assert_called_once()


def test_smtp_delivery_failure_has_generic_error_and_no_sensitive_log(monkeypatch, caplog):
    monkeypatch.setattr(settings, "smtp_user", "mail-user")
    monkeypatch.setattr(settings, "smtp_password", "smtp-password-fixture")
    with patch("app.services.email_service.smtplib.SMTP", side_effect=OSError("no connection")):
        with pytest.raises(EmailUnavailableError):
            EmailService().send_login_code("user@example.com", "123456", 10)
    assert "smtp-password-fixture" not in caplog.text and "123456" not in caplog.text


def test_otp_disabled_by_default_configuration(monkeypatch):
    monkeypatch.setattr(settings, "external_email_login_enabled", False)
    with pytest.raises(external_auth_service.ExternalAuthError, match="external_auth_unavailable"):
        external_auth_service.request_external_login_code(FakeSession(), "user@example.com", mailer=FakeMailer())


def test_no_real_email_is_sent_by_service_unit_tests(monkeypatch):
    captured = setup_request_repositories(monkeypatch)
    mailer = FakeMailer()
    external_auth_service.request_external_login_code(FakeSession(), "test@example.com", mailer=mailer)
    assert len(mailer.sent) == 1 and len(captured["codes"]) == 1
