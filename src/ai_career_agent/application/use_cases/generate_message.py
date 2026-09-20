from ai_career_agent.domain.entities import JobOffer, MessageDraft
from ai_career_agent.domain.ports import LLMClient


class GenerateMessageUseCase:
    """Genera drafts WOW para ofertas verdes o naranjas; caso de uso especializado."""

    def __init__(self, llm_client: LLMClient, cv_text: str):
        self.llm_client = llm_client
        self.cv_text = cv_text

    async def execute(self, offer: JobOffer) -> MessageDraft:
        return await self.llm_client.generate_message(offer, self.cv_text)
