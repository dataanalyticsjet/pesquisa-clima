from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pesquisa de Clima"
    app_env: str = "development"
    app_debug: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = 8002

    db_host: str = ""
    db_port: int = 3306
    db_name: str = "pesquisa_clima"
    db_user: str = ""
    db_password: str = ""

    feishu_oauth_enabled: bool = False
    feishu_oauth_app_id: str = ""
    feishu_oauth_app_secret: str = ""
    feishu_oauth_authorize_url: str = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
    feishu_oauth_token_url: str = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    feishu_oauth_userinfo_url: str = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    feishu_oauth_redirect_uri: str = ""
    frontend_base_url: str = ""
    allowed_corporate_domains: str = "jtexpress.com.br"

    session_secret: str = ""
    session_cookie_name: str = "pesquisa_clima_session"
    session_max_age_seconds: int = 28800
    session_secure: bool = False

    external_email_login_enabled: bool = False
    auth_code_ttl_minutes: int = Field(default=10, ge=1, le=30)
    auth_code_max_attempts: int = Field(default=5, ge=1, le=10)
    auth_code_resend_seconds: int = Field(default=60, ge=10, le=600)
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_ssl: bool = False
    smtp_starttls: bool = True
    smtp_timeout_seconds: int = Field(default=10, ge=1, le=60)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_mail_transport(self) -> "Settings":
        self.app_env = self.app_env.strip().lower()
        if self.app_env in {"production", "prod"} and self.app_debug:
            raise ValueError("APP_DEBUG must be disabled in production.")
        if self.smtp_ssl and self.smtp_starttls:
            raise ValueError("SMTP_SSL and SMTP_STARTTLS cannot both be enabled.")
        return self

    @property
    def smtp_configured(self) -> bool:
        credentials_valid = bool(self.smtp_user and self.smtp_password) or not (
            self.smtp_user or self.smtp_password
        )
        return bool(self.smtp_host and self.smtp_from and credentials_valid)

    @property
    def corporate_domain_allowlist(self) -> set[str]:
        return {
            domain.strip().lower().removeprefix("@")
            for domain in self.allowed_corporate_domains.split(",")
            if domain.strip()
        }


settings = Settings()
