from abc import ABC, abstractmethod
from typing import List

from ai_career_agent.domain.entities import JobOffer, MessageDraft


class JobScraper(ABC):
    """Puerto para el scraper; como un interface repository en TypeScript."""

    @abstractmethod
    async def fetch(self, search_url: str, max_offers: int) -> List[JobOffer]:
        """Extrae ofertas desde una URL de búsqueda."""
        raise NotImplementedError


class LLMClient(ABC):
    """Puerto para cualquier cliente de lenguaje; idem a un provider interface."""

    @abstractmethod
    async def evaluate(self, offer: JobOffer) -> JobOffer:
        """Evalúa una oferta y devuelve la entidad con score."""
        raise NotImplementedError

    @abstractmethod
    async def generate_message(self, offer: JobOffer, cv_text: str) -> MessageDraft:
        """Genera un draft personalizado para la oferta."""
        raise NotImplementedError


class OfferRepository(ABC):
    """Puerto para persistencia de ofertas; análogo a un Repository de TypeORM/Prisma."""

    @abstractmethod
    def count_today(self) -> int:
        """Cuenta ofertas procesadas hoy en la zona horaria configurada."""
        raise NotImplementedError

    @abstractmethod
    def save(self, offer: JobOffer) -> None:
        """Guarda o actualiza una oferta."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, offer_id: str) -> bool:
        """Indica si la oferta ya fue procesada."""
        raise NotImplementedError

    @abstractmethod
    def find_today(self) -> list[tuple[JobOffer, str | None]]:
        """Devuelve ofertas procesadas hoy y su draft (si existe)."""
        raise NotImplementedError

    @abstractmethod
    def save_draft(self, offer_id: str, draft_content: str) -> None:
        """Guarda el draft generado para una oferta."""
        raise NotImplementedError


class MessagePresenter(ABC):
    """Puerto para presentar resultados; como un controller/formatter."""

    @abstractmethod
    def show(self, offer: JobOffer, draft: MessageDraft | None) -> None:
        """Muestra el resultado de una oferta evaluada."""
        raise NotImplementedError
