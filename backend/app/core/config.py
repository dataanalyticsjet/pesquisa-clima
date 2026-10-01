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

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
