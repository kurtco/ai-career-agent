from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del agente cargada desde .env, como un ConfigService de Nest."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

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
    company_blacklist: list[str] = Field(default_factory=list)

    @field_validator("company_blacklist", mode="before")
    @classmethod
    def _split_blacklist(cls, value):
        """Permite COMPANY_BLACKLIST=BairesDev,Solvd,GlobalLogic en .env."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
