from ai_career_agent.domain.entities import JobOffer, MessageDraft, Score
from ai_career_agent.domain.ports import MessagePresenter


class ConsolePresenter(MessagePresenter):
    """Muestra resultados en consola; como un logger formateado de Nest."""

    def show(self, offer: JobOffer, draft: MessageDraft | None) -> None:
        emoji = {"red": "🔴", "orange": "🟠", "green": "🟢"}.get(offer.score.value, "⚪")
        print(f"\n{emoji} {offer.title} @ {offer.company}")
        print(f"   Score: {offer.score.value}")
        print(f"   Razón: {offer.reason}")
        print(f"   URL: {offer.url}")
        if draft:
            print(f"\n💬 Draft ({len(draft.content)} chars):\n{draft.content}\n")
