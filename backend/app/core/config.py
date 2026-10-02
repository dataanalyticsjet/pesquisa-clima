from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pesquisa de Clima"
    app_env: str = "development"
    app_debug: bool = True

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

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def corporate_domain_allowlist(self) -> set[str]:
        return {
            domain.strip().lower().removeprefix("@")
            for domain in self.allowed_corporate_domains.split(",")
            if domain.strip()
        }


settings = Settings()
