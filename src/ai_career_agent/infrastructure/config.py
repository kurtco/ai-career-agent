from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del agente cargada desde .env, como un ConfigService de Nest."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-lite"

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-flash"

    daily_offer_limit: int = 30
    timezone: str = "America/Bogota"
    db_path: Path = Path("data/history.db")
    session_state_path: Path = Path("data/session_state.json")
    cv_path: Path = Path("data/cv.md")
    linkedin_search_url: str = (
        "https://www.linkedin.com/jobs/search/?f_TPR=r86400&keywords=typescript"
    )


settings = Settings()
