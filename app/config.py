from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./research_mvp.db"
    llm_provider: str = "heuristic"
    codex_cli_command: str = "codex"
    codex_cli_model: str = ""
    codex_cli_timeout_seconds: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
