from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pesquisa de Clima"
    app_env: str = "development"
    app_debug: bool = True

    api_host: str = "127.0.0.1"
    api_port: int = 8002

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()