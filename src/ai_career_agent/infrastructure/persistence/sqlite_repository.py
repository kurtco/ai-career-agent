import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ai_career_agent.domain.entities import JobOffer, Score
from ai_career_agent.domain.ports import OfferRepository


class SqliteOfferRepository(OfferRepository):
    """Persistencia SQLite del límite diario; como un TypeORM repository concreto."""

    def __init__(self, db_path: Path, timezone: str = "America/Bogota"):
        self.db_path = db_path
        self.timezone = timezone
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS offers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    score TEXT NOT NULL,
                    processed_at_utc TEXT NOT NULL,
                    processed_date_local TEXT NOT NULL
                )
                """
            )

    def count_today(self) -> int:
        today = self._today_local()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM offers WHERE processed_date_local = ?",
                (today.isoformat(),),
            ).fetchone()
            return row[0] if row else 0

    def exists(self, offer_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM offers WHERE id = ?", (offer_id,)
            ).fetchone()
            return row is not None

    def save(self, offer: JobOffer) -> None:
        processed_at = offer.processed_at or datetime.now(timezone.utc)
        if processed_at.tzinfo is None:
            processed_at = processed_at.replace(tzinfo=ZoneInfo("UTC"))
        date_local = processed_at.astimezone(ZoneInfo(self.timezone)).date()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO offers
                (id, title, company, score, processed_at_utc, processed_date_local)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    offer.id,
                    offer.title,
                    offer.company,
                    offer.score.value,
                    processed_at.isoformat(),
                    date_local.isoformat(),
                ),
            )

    def _today_local(self) -> date:
        return datetime.now(ZoneInfo(self.timezone)).date()
