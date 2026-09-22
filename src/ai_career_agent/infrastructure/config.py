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
    gemini_model: str = "gemini-3.5-flash-lite"

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-flash"

    daily_offer_limit: int = 30
    timezone: str = "America/Bogota"
    db_path: Path = Path("data/history.db")
    session_state_path: Path = Path("data/session_state.json")
    cv_path: Path = Path("data/cv.md")
    reports_dir: Path = Path("data/reports")
    auto_open_report: bool = True
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8000
    linkedin_search_url: str = (
        "https://www.linkedin.com/jobs/search/?keywords=typescript"
    )
    linkedin_export_path: Path = Path("data/linkedin_export")
    company_blacklist: str = ""

    def company_blacklist_list(self) -> list[str]:
        """Parsea COMPANY_BLACKLIST=BairesDev,Solvd en lista."""
        return [item.strip() for item in self.company_blacklist.split(",") if item.strip()]


settings = Settings()
