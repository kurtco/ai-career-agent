from datetime import datetime, timezone

from ai_career_agent.domain.entities import JobOffer
from ai_career_agent.domain.ports import LLMClient, OfferRepository


class EvaluateJobUseCase:
    """Evalúa una oferta contra filtros vía LLM; como un CommandHandler de Nest."""

    def __init__(self, llm_client: LLMClient, repository: OfferRepository):
        self.llm_client = llm_client
        self.repository = repository

    async def execute(self, offer: JobOffer) -> JobOffer:
        scored = await self.llm_client.evaluate(offer)
        scored.processed_at = datetime.now(timezone.utc)
        self.repository.save(scored)
        return scored
