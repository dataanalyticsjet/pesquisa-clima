from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class FeishuIdentity:
    name: str | None
    email: str | None
    enterprise_email: str | None
    open_id: str | None
    union_id: str | None


class FeishuOAuthError(Exception):
    pass


class FeishuTokenExchangeError(FeishuOAuthError):
    pass


class FeishuUserInfoError(FeishuOAuthError):
    pass


class FeishuOAuthClient:
    def __init__(self, *, token_url: str, userinfo_url: str, app_id: str, app_secret: str):
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.app_id = app_id
        self.app_secret = app_secret

    def get_identity(self, code: str, redirect_uri: str) -> FeishuIdentity:
        try:
            with httpx.Client(timeout=10.0) as client:
                token_response = client.post(
                    self.token_url,
                    json={
                        "grant_type": "authorization_code",
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                )
                token_response.raise_for_status()
                token_payload = token_response.json()
                access_token = token_payload.get("access_token")
                if token_payload.get("code", 0) != 0 or not isinstance(access_token, str) or not access_token:
                    raise FeishuTokenExchangeError("token exchange failed")
        except FeishuOAuthError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            raise FeishuTokenExchangeError("token exchange failed") from None

        try:
            with httpx.Client(timeout=10.0) as client:
                user_response = client.get(
                    self.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                user_response.raise_for_status()
                user_payload = user_response.json()
                if user_payload.get("code", 0) != 0 or not isinstance(user_payload.get("data"), dict):
                    raise FeishuUserInfoError("userinfo request failed")
                data = user_payload["data"]
                return FeishuIdentity(
                    name=data.get("name"),
                    email=data.get("email"),
                    enterprise_email=data.get("enterprise_email"),
                    open_id=data.get("open_id"),
                    union_id=data.get("union_id"),
                )
        except FeishuOAuthError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            raise FeishuUserInfoError("userinfo request failed") from None
