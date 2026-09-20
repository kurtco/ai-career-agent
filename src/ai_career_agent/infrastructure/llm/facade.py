from ai_career_agent.domain.entities import JobOffer, MessageDraft
from ai_career_agent.domain.ports import LLMClient


try:
    from google.genai.errors import APIError as GeminiAPIError
except Exception:  # pragma: no cover - depende de la versión del SDK
    GeminiAPIError = Exception


try:
    from openai import RateLimitError, APIError as OpenAIAPIError
except Exception:  # pragma: no cover
    RateLimitError = Exception
    OpenAIAPIError = Exception


class LLMClientFacade(LLMClient):
    """Intenta Gemini; ante rate limit o 5xx cae a DeepSeek, como un circuito manual."""

    def __init__(self, primary: LLMClient, fallback: LLMClient):
        self.primary = primary
        self.fallback = fallback

    async def evaluate(self, offer: JobOffer) -> JobOffer:
        try:
            return await self.primary.evaluate(offer)
        except (GeminiAPIError, RateLimitError, OpenAIAPIError) as exc:
            if not self._should_fallback(exc):
                raise
            return await self.fallback.evaluate(offer)

    async def generate_message(self, offer: JobOffer, cv_text: str) -> MessageDraft:
        try:
            return await self.primary.generate_message(offer, cv_text)
        except (GeminiAPIError, RateLimitError, OpenAIAPIError) as exc:
            if not self._should_fallback(exc):
                raise
            return await self.fallback.generate_message(offer, cv_text)

    def _should_fallback(self, exc: Exception) -> bool:
        status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if isinstance(exc, RateLimitError):
            return True
        if isinstance(status, int) and status >= 500:
            return True
        # Algunos errores de Gemini vienen como 429 sin status_code explícito.
        if "429" in str(exc) or "rate limit" in str(exc).lower():
            return True
        return False
