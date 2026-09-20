import argparse
import asyncio
import sys
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ai_career_agent.adapters.presenter import ConsolePresenter
from ai_career_agent.application.use_cases.evaluate_job import EvaluateJobUseCase
from ai_career_agent.application.use_cases.fetch_offers import FetchOffersUseCase
from ai_career_agent.application.use_cases.generate_message import GenerateMessageUseCase
from ai_career_agent.domain.entities import Score
from ai_career_agent.domain.ports import LLMClient
from ai_career_agent.infrastructure.config import settings
from ai_career_agent.infrastructure.llm.deepseek_client import DeepSeekClient
from ai_career_agent.infrastructure.llm.facade import LLMClientFacade
from ai_career_agent.infrastructure.llm.gemini_client import GeminiClient
from ai_career_agent.infrastructure.persistence.sqlite_repository import (
    SqliteOfferRepository,
)
from ai_career_agent.infrastructure.scraper.playwright_linkedin import (
    PlaywrightLinkedInScraper,
)


def build_llm_client() -> LLMClient:
    """Compone el cliente LLM con fallback; como el providers array de Nest."""
    primary = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
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
    )

    cv_text = ""
    if settings.cv_path.exists():
        cv_text = settings.cv_path.read_text(encoding="utf-8")
    generate_use_case = GenerateMessageUseCase(llm_client, cv_text)
    presenter = ConsolePresenter()

    offers = await fetch_use_case.execute(settings.linkedin_search_url)
    for offer in offers:
        draft = None
        if offer.score in (Score.GREEN, Score.ORANGE):
            draft = await generate_use_case.execute(offer)
        presenter.show(offer, draft)


async def run_scheduler() -> None:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(run_once, CronTrigger(hour=9, minute=0))
    scheduler.start()
    print(f"Scheduler iniciado. Ejecutará todos los días a las 9:00 AM {settings.timezone}")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Career Agent")
    parser.add_argument("--now", action="store_true", help="Ejecuta una vez ahora")
    args = parser.parse_args()

    if args.now:
        asyncio.run(run_once())
    else:
        asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
