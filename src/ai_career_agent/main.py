import argparse
import asyncio
import sys
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ai_career_agent.adapters.html_report import HtmlReportGenerator
from ai_career_agent.adapters.presenter import ConsolePresenter
from ai_career_agent.application.use_cases.evaluate_job import EvaluateJobUseCase
from ai_career_agent.application.use_cases.fetch_offers import FetchOffersUseCase
from ai_career_agent.application.use_cases.generate_message import GenerateMessageUseCase
from ai_career_agent.domain.entities import MessageDraft, Score
from ai_career_agent.domain.ports import LLMClient
from ai_career_agent.infrastructure.config import settings
from ai_career_agent.infrastructure.dashboard.flask_app import run_dashboard
from ai_career_agent.infrastructure.llm.deepseek_client import DeepSeekClient
from ai_career_agent.infrastructure.llm.facade import LLMClientFacade
from ai_career_agent.infrastructure.llm.gemini_client import GeminiClient
from ai_career_agent.infrastructure.parsers.linkedin_job_alerts_parser import (
    LinkedInJobAlertsParser,
)
from ai_career_agent.infrastructure.persistence.sqlite_repository import (
    SqliteOfferRepository,
)
from ai_career_agent.infrastructure.scraper.playwright_linkedin import (
    PlaywrightLinkedInScraper,
)


def build_llm_client() -> LLMClient:
    """Compone el cliente LLM; fallback opcional si hay saldo en DeepSeek."""
    primary = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if not settings.deepseek_api_key:
        return primary
    fallback = DeepSeekClient(
        api_key=settings.deepseek_api_key, model=settings.deepseek_model
    )
    return LLMClientFacade(primary=primary, fallback=fallback)


async def run_once() -> None:
    if not settings.gemini_api_key and not settings.deepseek_api_key:
        print(
            "Error: no hay API keys configuradas. Copia .env.example a .env y añade GEMINI_API_KEY o DEEPSEEK_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    repository = SqliteOfferRepository(settings.db_path, settings.timezone)
    llm_client = build_llm_client()
    evaluate_use_case = EvaluateJobUseCase(llm_client, repository)
    scraper = PlaywrightLinkedInScraper(settings.session_state_path)
    fetch_use_case = FetchOffersUseCase(
        scraper=scraper,
        repository=repository,
        evaluate_use_case=evaluate_use_case,
        daily_limit=settings.daily_offer_limit,
        company_blacklist=settings.company_blacklist_list(),
    )

    cv_text = ""
    if settings.cv_path.exists():
        cv_text = settings.cv_path.read_text(encoding="utf-8")
    generate_use_case = GenerateMessageUseCase(llm_client, cv_text)
    presenter = ConsolePresenter()
    report = HtmlReportGenerator(settings.reports_dir, auto_open=settings.auto_open_report)

    search_urls = [settings.linkedin_search_url]
    alerts_parser = LinkedInJobAlertsParser(settings.linkedin_export_path)
    alert_urls = alerts_parser.parse_search_urls()
    search_urls.extend(alert_urls)

    for search_url in search_urls:
        if repository.count_today() >= settings.daily_offer_limit:
            break
        offers = await fetch_use_case.execute(search_url)
        for offer in offers:
            draft = None
            if offer.score in (Score.GREEN, Score.ORANGE):
                draft = await generate_use_case.execute(offer)
                repository.save_draft(offer.id, draft.content)
            presenter.show(offer, draft)
            report.add(offer, draft)

    if report._entries:
        report_path = report.generate()
        print(f"\n📄 Reporte HTML: {report_path}")


async def run_scheduler() -> None:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(run_once, CronTrigger(hour=9, minute=0))
    scheduler.start()
    print(f"Scheduler iniciado. Ejecutará todos los días a las 9:00 AM {settings.timezone}")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


async def generate_report_only() -> None:
    """Genera el reporte HTML desde todo el historial sin hacer scraping."""
    repository = SqliteOfferRepository(settings.db_path, settings.timezone)
    entries = repository.find_all_offers()
    if not entries:
        print("No hay ofertas guardadas para generar el reporte.")
        return

    report = HtmlReportGenerator(settings.reports_dir, auto_open=settings.auto_open_report)
    for offer, draft_content in entries:
        draft = MessageDraft(offer_id=offer.id, content=draft_content) if draft_content else None
        report.add(offer, draft)

    report_path = report.generate()
    print(f"\n📄 Reporte HTML: {report_path}")


def run_dashboard_server() -> None:
    """Levanta el servidor Flask del dashboard interactivo."""
    run_dashboard(settings.dashboard_host, settings.dashboard_port)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Career Agent")
    parser.add_argument("--now", action="store_true", help="Ejecuta una vez ahora")
    parser.add_argument(
        "--no-open",
        dest="no_open",
        action="store_true",
        help="No abre el reporte HTML automáticamente",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Genera el reporte HTML desde todo el historial sin nueva búsqueda",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Inicia el servidor web interactivo del dashboard",
    )
    args = parser.parse_args()

    if args.no_open:
        settings.auto_open_report = False

    if args.report_only:
        asyncio.run(generate_report_only())
    elif args.dashboard:
        run_dashboard_server()
    elif args.now:
        asyncio.run(run_once())
    else:
        asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
