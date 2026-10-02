import base64
import json
import time
from contextlib import contextmanager
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core import auth as auth_core
from app.core.config import settings
from app.main import app
from app.models.identity import User
from app.repositories import identity_repository
from app.services import identity_service
from app.services.feishu_oauth import FeishuIdentity, FeishuTokenExchangeError, FeishuUserInfoError


client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def oauth_settings(monkeypatch):
    client.cookies.clear()
    monkeypatch.setattr(settings, "feishu_oauth_enabled", True)
    monkeypatch.setattr(settings, "feishu_oauth_app_id", "cli_test_id")
    monkeypatch.setattr(settings, "feishu_oauth_app_secret", "secret-for-tests")
    monkeypatch.setattr(settings, "feishu_oauth_authorize_url", "https://accounts.feishu.cn/open-apis/authen/v1/authorize")
    monkeypatch.setattr(settings, "feishu_oauth_token_url", "https://open.feishu.cn/open-apis/authen/v2/oauth/token")
    monkeypatch.setattr(settings, "feishu_oauth_userinfo_url", "https://open.feishu.cn/open-apis/authen/v1/user_info")
    monkeypatch.setattr(settings, "feishu_oauth_redirect_uri", "http://127.0.0.1:8002/api/auth/feishu/callback")
    monkeypatch.setattr(settings, "frontend_base_url", "http://127.0.0.1:3001/login")
    monkeypatch.setattr(settings, "allowed_corporate_domains", "jtexpress.com.br")
    yield
    client.cookies.clear()


def decode_cookie_session(test_client):
    cookie = test_client.cookies.get(settings.session_cookie_name)
    assert cookie
    encoded = cookie.split(".", 1)[0]
    return json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))


def login_and_capture_state(test_client=client):
    response = test_client.get("/api/auth/feishu/login")
    assert response.status_code == 302
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    return response, state


def test_login_redirects_to_feishu_with_current_authorize_parameters():
    response, state = login_and_capture_state()
    params = parse_qs(urlparse(response.headers["location"]).query)
    assert urlparse(response.headers["location"]).netloc == "accounts.feishu.cn"
    assert params["client_id"] == ["cli_test_id"]
    assert params["response_type"] == ["code"]
    assert params["redirect_uri"] == [settings.feishu_oauth_redirect_uri]
    assert params["state"] == [state]


def test_login_creates_cryptographically_sized_state_in_signed_session():
    login_and_capture_state()
    session = decode_cookie_session(client)
    assert len(session[auth_api.STATE_SESSION_KEY]) >= 40
    assert isinstance(session[auth_api.STATE_ISSUED_SESSION_KEY], int)


def test_login_returns_only_state_metadata_in_transient_cookie():
    login_and_capture_state()
    session = decode_cookie_session(client)
    assert set(session) == {auth_api.STATE_SESSION_KEY, auth_api.STATE_ISSUED_SESSION_KEY}
    assert "secret-for-tests" not in client.cookies.get(settings.session_cookie_name)


def test_login_disabled_redirects_with_generic_error(monkeypatch):
    monkeypatch.setattr(settings, "feishu_oauth_enabled", False)
    response = client.get("/api/auth/feishu/login")
    assert response.status_code == 303
    assert "auth_error=feishu_disabled" in response.headers["location"]


@pytest.mark.parametrize("provided_state", ["wrong", "", None])
def test_callback_rejects_invalid_state_without_contacting_feishu(monkeypatch, provided_state):
    class NeverFeishu:
        def __init__(self, **kwargs):
            raise AssertionError("Feishu must not be called")

    monkeypatch.setattr(auth_api, "FeishuOAuthClient", NeverFeishu)
    _, expected = login_and_capture_state()
    response = client.get("/api/auth/feishu/callback", params={"code": "fake", "state": provided_state or ""})
    assert response.status_code == 303
    assert "auth_error=invalid_state" in response.headers["location"]
    assert expected not in client.cookies.get(settings.session_cookie_name, "")


def test_callback_rejects_expired_state(monkeypatch):
    _, state = login_and_capture_state()
    original_time = time.time
    monkeypatch.setattr(auth_api.time, "time", lambda: int(original_time()) + auth_api.STATE_TTL_SECONDS + 1)
    response = client.get("/api/auth/feishu/callback", params={"code": "fake", "state": state})
    assert response.status_code == 303
    assert "auth_error=expired_state" in response.headers["location"]


@pytest.mark.parametrize("code", [None, ""])
def test_callback_requires_code(monkeypatch, code):
    class NeverFeishu:
        def __init__(self, **kwargs):
            raise AssertionError("Feishu must not be called")

    monkeypatch.setattr(auth_api, "FeishuOAuthClient", NeverFeishu)
    _, state = login_and_capture_state()
    params = {"state": state}
    if code is not None:
        params["code"] = code
    response = client.get("/api/auth/feishu/callback", params=params)
    assert "auth_error=missing_code" in response.headers["location"]


@pytest.mark.parametrize(
    "error,expected_code",
    [(FeishuTokenExchangeError(), "token_exchange_failed"), (FeishuUserInfoError(), "userinfo_failed")],
)
def test_callback_maps_feishu_errors_without_exposing_details(monkeypatch, error, expected_code):
    class FailedFeishu:
        def __init__(self, **kwargs):
            pass

        def get_identity(self, code, redirect_uri):
            raise error

    monkeypatch.setattr(auth_api, "FeishuOAuthClient", FailedFeishu)
    _, state = login_and_capture_state()
    response = client.get("/api/auth/feishu/callback", params={"code": "mock-code", "state": state})
    assert f"auth_error={expected_code}" in response.headers["location"]
    assert "secret-for-tests" not in response.text
    assert "mock-code" not in response.headers["location"]


class FakeSession:
    def __init__(self):
        self.closed = False
        self.committed = False
        self.rolled_back = False

    @contextmanager
    def begin(self):
        try:
            yield self
            self.committed = True
        except Exception:
            self.rolled_back = True
            raise

    def close(self):
        self.closed = True


def patch_callback_success(monkeypatch, identity=None):
    identity = identity or FeishuIdentity("Colaborador", "user@jtexpress.com.br", None, "open-1", "union-1")

    class MockFeishu:
        def __init__(self, **kwargs):
            self.config = kwargs

        def get_identity(self, code, redirect_uri):
            assert code == "mock-code"
            assert redirect_uri == settings.feishu_oauth_redirect_uri
            return identity

    session = FakeSession()
    monkeypatch.setattr(auth_api, "FeishuOAuthClient", MockFeishu)
    monkeypatch.setattr(auth_api, "SessionLocal", lambda: session)
    monkeypatch.setattr(auth_api, "provision_internal_user", lambda db, profile: SimpleNamespace(id=91))
    return session


def test_callback_exchanges_mock_code_and_sets_local_session(monkeypatch):
    session = patch_callback_success(monkeypatch)
    _, state = login_and_capture_state()
    response = client.get("/api/auth/feishu/callback", params={"code": "mock-code", "state": state})
    assert response.status_code == 303
    frontend = urlparse(settings.frontend_base_url)
    assert response.headers["location"] == f"{frontend.scheme}://{frontend.netloc}/home"
    assert session.committed and session.closed
    assert decode_cookie_session(client) == {"user_id": 91}


def test_callback_does_not_return_token_or_user_identity_ids(monkeypatch):
    patch_callback_success(monkeypatch)
    _, state = login_and_capture_state()
    response = client.get("/api/auth/feishu/callback", params={"code": "mock-code", "state": state})
    assert "access_token" not in response.text
    assert "refresh_token" not in response.text
    assert "open_id" not in response.text
    assert "union_id" not in response.text


def test_callback_rolls_back_on_local_provisioning_error(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(auth_api, "SessionLocal", lambda: session)
    monkeypatch.setattr(auth_api, "provision_internal_user", lambda db, profile: (_ for _ in ()).throw(identity_service.AuthFlowError("unauthorized_domain")))

    class MockFeishu:
        def __init__(self, **kwargs): pass
        def get_identity(self, code, redirect_uri): return FeishuIdentity("N", "x@other.com", None, None, None)

    monkeypatch.setattr(auth_api, "FeishuOAuthClient", MockFeishu)
    _, state = login_and_capture_state()
    response = client.get("/api/auth/feishu/callback", params={"code": "mock-code", "state": state})
    assert "auth_error=unauthorized_domain" in response.headers["location"]
    assert session.rolled_back and session.closed


@pytest.mark.parametrize(
    "profile,expected",
    [
        (FeishuIdentity("Nome", "fallback@jtexpress.com.br", " PHELIPPE.CARDOSO@JTEXPRESS.COM.BR ", None, None), "phelippe.cardoso@jtexpress.com.br"),
        (FeishuIdentity("Nome", " PHELIPPE.CARDOSO@JTEXPRESS.COM.BR ", None, None, None), "phelippe.cardoso@jtexpress.com.br"),
    ],
)
def test_email_resolution_priority_and_normalization(profile, expected):
    assert identity_service.resolve_corporate_email(profile) == expected


@pytest.mark.parametrize("domain", ["gmail.com", "jtexpress.com", "sub.jtexpress.com.br", "jtexpress.com.br.evil.org"])
def test_email_resolution_rejects_unapproved_domains(domain):
    with pytest.raises(identity_service.AuthFlowError, match="unauthorized_domain"):
        identity_service.resolve_corporate_email(FeishuIdentity("Name", f"user@{domain}", None, None, None))


@pytest.mark.parametrize("email", [None, "", "  ", "missing-at-domain", "@jtexpress.com.br", "name@"])
def test_email_resolution_rejects_missing_or_malformed_email(email):
    with pytest.raises(identity_service.AuthFlowError, match="email_not_found"):
        identity_service.resolve_corporate_email(FeishuIdentity("Name", email, None, None, None))


def fake_identity_repositories(monkeypatch, existing=None, id_match=None, role=SimpleNamespace(id=3, code="COLLABORATOR")):
    state = {"created": None, "role_added": [], "existing": existing, "id_match": id_match}
    monkeypatch.setattr(identity_repository, "get_user_by_email", lambda session, email: state["existing"])
    monkeypatch.setattr(identity_repository, "get_users_by_feishu_ids", lambda session, open_id, union_id: [state["id_match"]] if state["id_match"] is not None else [])
    monkeypatch.setattr(identity_repository, "add_user", lambda session, **kwargs: state.update(created=SimpleNamespace(id=12, **kwargs, feishu_open_id=kwargs["open_id"], feishu_union_id=kwargs["union_id"], status="ACTIVE", access_type="INTERNAL", last_login_at=None)) or state["created"])
    monkeypatch.setattr(identity_repository, "get_role_by_code", lambda session, code: role if code == "COLLABORATOR" else None)
    monkeypatch.setattr(identity_repository, "add_user_role", lambda session, user_id, role_id: state["role_added"].append((user_id, role_id)))
    return state


def test_existing_user_preserves_account_and_roles_and_sets_login_time(monkeypatch):
    user = SimpleNamespace(id=8, email="p@jtexpress.com.br", name="Original", access_type="INTERNAL", status="ACTIVE", feishu_open_id=None, feishu_union_id=None, last_login_at=None)
    fake_identity_repositories(monkeypatch, existing=user)
    result = identity_service.provision_internal_user(object(), FeishuIdentity("Changed", "p@jtexpress.com.br", None, "open", "union"))
    assert result is user
    assert user.name == "Original" and user.access_type == "INTERNAL" and user.status == "ACTIVE"
    assert user.feishu_open_id == "open" and user.feishu_union_id == "union"
    assert user.last_login_at is not None


def test_existing_admin_role_is_not_changed_or_replaced(monkeypatch):
    user = SimpleNamespace(id=8, email="p@jtexpress.com.br", name="Admin", access_type="INTERNAL", status="ACTIVE", feishu_open_id="open", feishu_union_id="union", last_login_at=None)
    state = fake_identity_repositories(monkeypatch, existing=user)
    assert identity_service.provision_internal_user(object(), FeishuIdentity("Admin", user.email, None, "open", "union")) is user
    assert state["role_added"] == []


@pytest.mark.parametrize("status", ["INACTIVE", "SUSPENDED"])
def test_non_active_existing_user_is_blocked_without_reactivation(monkeypatch, status):
    user = SimpleNamespace(id=1, email="p@jtexpress.com.br", status=status, access_type="INTERNAL", feishu_open_id=None, feishu_union_id=None, last_login_at=None)
    fake_identity_repositories(monkeypatch, existing=user)
    with pytest.raises(identity_service.AuthFlowError, match="user_inactive"):
        identity_service.provision_internal_user(object(), FeishuIdentity("N", user.email, None, None, None))
    assert user.status == status


def test_existing_external_user_is_not_silently_converted(monkeypatch):
    user = SimpleNamespace(id=1, email="p@jtexpress.com.br", status="ACTIVE", access_type="EXTERNAL", feishu_open_id=None, feishu_union_id=None, last_login_at=None)
    fake_identity_repositories(monkeypatch, existing=user)
    with pytest.raises(identity_service.AuthFlowError, match="identity_conflict"):
        identity_service.provision_internal_user(object(), FeishuIdentity("N", user.email, None, None, None))
    assert user.access_type == "EXTERNAL"


@pytest.mark.parametrize("field,old_value,new_value", [("feishu_open_id", "old-open", "new-open"), ("feishu_union_id", "old-union", "new-union")])
def test_existing_feishu_id_mismatch_is_rejected(monkeypatch, field, old_value, new_value):
    user = SimpleNamespace(id=1, email="p@jtexpress.com.br", status="ACTIVE", access_type="INTERNAL", feishu_open_id=None, feishu_union_id=None, last_login_at=None)
    setattr(user, field, old_value)
    fake_identity_repositories(monkeypatch, existing=user)
    values = {"open_id": "same-open", "union_id": "same-union"}
    values["open_id" if field == "feishu_open_id" else "union_id"] = new_value
    with pytest.raises(identity_service.AuthFlowError, match="identity_conflict"):
        identity_service.provision_internal_user(object(), FeishuIdentity("N", user.email, None, **values))


def test_feishu_id_linked_to_another_account_is_rejected(monkeypatch):
    matching_email = SimpleNamespace(id=1, email="p@jtexpress.com.br", status="ACTIVE", access_type="INTERNAL", feishu_open_id=None, feishu_union_id=None, last_login_at=None)
    other = SimpleNamespace(id=2)
    fake_identity_repositories(monkeypatch, existing=matching_email, id_match=other)
    with pytest.raises(identity_service.AuthFlowError, match="identity_conflict"):
        identity_service.provision_internal_user(object(), FeishuIdentity("N", matching_email.email, None, "claimed", None))


def test_new_user_is_internal_active_and_gets_only_collaborator(monkeypatch):
    state = fake_identity_repositories(monkeypatch)
    user = identity_service.provision_internal_user(object(), FeishuIdentity(" Novo ", "x@jtexpress.com.br", None, "open", "union"))
    assert user.id == 12 and user.email == "x@jtexpress.com.br" and user.name == "Novo"
    assert user.status == "ACTIVE" and user.access_type == "INTERNAL"
    assert user.feishu_open_id == "open" and user.feishu_union_id == "union"
    assert state["role_added"] == [(12, 3)]


@pytest.mark.parametrize("ids", [(None, None), ("open-only", None), (None, "union-only")])
def test_new_user_supports_optional_feishu_ids(monkeypatch, ids):
    state = fake_identity_repositories(monkeypatch)
    user = identity_service.provision_internal_user(object(), FeishuIdentity("N", "x@jtexpress.com.br", None, *ids))
    assert user.feishu_open_id == ids[0] and user.feishu_union_id == ids[1]
    assert state["role_added"] == [(12, 3)]


def test_new_user_requires_name_without_using_name_as_identity(monkeypatch):
    state = fake_identity_repositories(monkeypatch)
    with pytest.raises(identity_service.AuthFlowError, match="identity_conflict"):
        identity_service.provision_internal_user(object(), FeishuIdentity(None, "x@jtexpress.com.br", None, None, None))
    assert state["created"] is None


def test_missing_collaborator_role_fails_new_provisioning(monkeypatch):
    state = fake_identity_repositories(monkeypatch, role=None)
    with pytest.raises(identity_service.AuthFlowError, match="session_creation_failed"):
        identity_service.provision_internal_user(object(), FeishuIdentity("N", "x@jtexpress.com.br", None, None, None))
    assert state["role_added"] == []


def test_me_without_session_returns_controlled_401():
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHENTICATED"}


def test_me_authenticated_returns_only_allowed_user_fields(monkeypatch):
    user = SimpleNamespace(id=44, name="Pessoa", email="p@jtexpress.com.br", access_type="INTERNAL", status="ACTIVE", feishu_open_id="secret-open", feishu_union_id="secret-union")
    monkeypatch.setattr(auth_core, "get_user_by_id", lambda session, user_id: user)
    monkeypatch.setattr(auth_api, "get_user_roles", lambda session, user_id: ["COLLABORATOR"])
    client.cookies.set(settings.session_cookie_name, "")
    _, state = login_and_capture_state()
    patch_callback_success(monkeypatch)
    response = client.get("/api/auth/me")
    assert response.status_code == 401  # state cookie is not an authenticated session
    client.cookies.clear()
    _, state = login_and_capture_state()
    patch_callback_success(monkeypatch)
    client.get("/api/auth/feishu/callback", params={"code": "mock-code", "state": state})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"authenticated": True, "user": {"name": "Pessoa", "email": user.email, "access_type": "INTERNAL", "roles": ["COLLABORATOR"]}}
    for secret in ("secret-open", "secret-union", "access_token", "refresh_token", "session_token"):
        assert secret not in response.text


def test_logout_clears_local_cookie_session():
    login_and_capture_state()
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}
    assert "expires=thu, 01 jan 1970" in response.headers.get("set-cookie", "").lower()


def test_cookie_security_attributes_are_present_after_login():
    response, _ = login_and_capture_state()
    cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert "max-age=" in cookie


def test_login_state_is_one_time(monkeypatch):
    class MockFeishu:
        def __init__(self, **kwargs): pass
        def get_identity(self, code, redirect_uri): return FeishuIdentity("N", "x@jtexpress.com.br", None, None, None)

    session = FakeSession()
    monkeypatch.setattr(auth_api, "FeishuOAuthClient", MockFeishu)
    monkeypatch.setattr(auth_api, "SessionLocal", lambda: session)
    monkeypatch.setattr(auth_api, "provision_internal_user", lambda db, profile: SimpleNamespace(id=5))
    _, state = login_and_capture_state()
    client.get("/api/auth/feishu/callback", params={"state": state, "code": "c"})
    second = client.get("/api/auth/feishu/callback", params={"state": state, "code": "c"})
    assert "auth_error=invalid_state" in second.headers["location"]


def test_callback_generic_failure_does_not_expose_exception_or_secret(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(auth_api, "SessionLocal", lambda: session)
    monkeypatch.setattr(auth_api, "provision_internal_user", lambda db, profile: (_ for _ in ()).throw(RuntimeError("DB host, password=secret-for-tests")))

    class MockFeishu:
        def __init__(self, **kwargs): pass
        def get_identity(self, code, redirect_uri): return FeishuIdentity("N", "x@jtexpress.com.br", None, None, None)

    monkeypatch.setattr(auth_api, "FeishuOAuthClient", MockFeishu)
    _, state = login_and_capture_state()
    response = client.get("/api/auth/feishu/callback", params={"code": "mock-code", "state": state})
    assert "auth_error=session_creation_failed" in response.headers["location"]
    assert "DB host" not in response.text and "secret-for-tests" not in response.text


def test_feishu_client_uses_mocked_official_token_and_userinfo_calls(monkeypatch):
    from app.services import feishu_oauth

    requests = []

    class FakeResponse:
        def __init__(self, payload): self.payload = payload
        def raise_for_status(self): pass
        def json(self): return self.payload

    class FakeHttpxClient:
        def __init__(self, timeout):
            assert timeout == 10.0
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, json):
            requests.append(("POST", url, json, None))
            return FakeResponse({"code": 0, "access_token": "private-access-token", "refresh_token": "private-refresh-token"})
        def get(self, url, headers):
            requests.append(("GET", url, None, headers))
            return FakeResponse({"code": 0, "data": {"name": "Colaborador", "enterprise_email": "person@jtexpress.com.br", "open_id": "openid-private", "union_id": "unionid-private"}})

    monkeypatch.setattr(feishu_oauth.httpx, "Client", FakeHttpxClient)
    oauth_client = feishu_oauth.FeishuOAuthClient(
        token_url=settings.feishu_oauth_token_url,
        userinfo_url=settings.feishu_oauth_userinfo_url,
        app_id="cli_test_id",
        app_secret="secret-for-tests",
    )
    identity = oauth_client.get_identity("code-mock", settings.feishu_oauth_redirect_uri)
    assert identity.enterprise_email == "person@jtexpress.com.br"
    assert [request[0] for request in requests] == ["POST", "GET"]
    token_request = requests[0][2]
    assert token_request == {
        "grant_type": "authorization_code",
        "client_id": "cli_test_id",
        "client_secret": "secret-for-tests",
        "code": "code-mock",
        "redirect_uri": settings.feishu_oauth_redirect_uri,
    }
    assert requests[1][3] == {"Authorization": "Bearer private-access-token"}


def test_feishu_client_maps_invalid_token_response_to_generic_error(monkeypatch):
    from app.services import feishu_oauth

    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return {"code": 999, "msg": "sensitive provider diagnostic"}

    class FakeHttpxClient:
        def __init__(self, timeout): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs): return FakeResponse()

    monkeypatch.setattr(feishu_oauth.httpx, "Client", FakeHttpxClient)
    oauth_client = feishu_oauth.FeishuOAuthClient(token_url="token", userinfo_url="user", app_id="id", app_secret="secret")
    with pytest.raises(FeishuTokenExchangeError) as error:
        oauth_client.get_identity("mock", "redirect")
    assert "sensitive provider diagnostic" not in str(error.value)

def test_blank_enterprise_email_falls_back_to_corporate_email():
    profile = FeishuIdentity("Nome", " PHELIPPE.CARDOSO@JTEXPRESS.COM.BR ", "   ", None, None)
    assert identity_service.resolve_corporate_email(profile) == "phelippe.cardoso@jtexpress.com.br"
