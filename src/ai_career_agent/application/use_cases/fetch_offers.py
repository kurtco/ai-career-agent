from datetime import datetime
from typing import List

from ai_career_agent.domain.entities import JobOffer
from ai_career_agent.domain.exceptions import BlockedError
from ai_career_agent.domain.ports import JobScraper, LLMClient, OfferRepository


class FetchOffersUseCase:
    """Obtiene ofertas respetando el límite diario; como un QueryHandler de Nest."""

    def __init__(
        self,
        scraper: JobScraper,
        repository: OfferRepository,
        evaluate_use_case,
        daily_limit: int = 30,
        company_blacklist: List[str] | None = None,
    ):
        self.scraper = scraper
        self.repository = repository
        self.evaluate_use_case = evaluate_use_case
        self.daily_limit = daily_limit
        self.company_blacklist = {c.lower() for c in (company_blacklist or [])}

    async def execute(self, search_url: str) -> List[JobOffer]:
        processed_today = self.repository.count_today()
        remaining = self.daily_limit - processed_today
        if remaining <= 0:
            return []

        try:
            offers = await self.scraper.fetch(search_url, remaining)
        except BlockedError:
            # Abortamos la corrida completa; el caso de uso no reintenta.
            return []

        evaluated: List[JobOffer] = []
        for offer in offers:
            if self._is_blacklisted(offer):
                continue
            if self.repository.exists(offer.id):
                continue
            scored = await self.evaluate_use_case.execute(offer)
            evaluated.append(scored)
        return evaluated

    def _is_blacklisted(self, offer: JobOffer) -> bool:
        return offer.company.strip().lower() in self.company_blacklist
