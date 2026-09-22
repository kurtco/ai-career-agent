import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple
from zoneinfo import ZoneInfo

from ai_career_agent.domain.entities import (
    CompensationPeriod,
    ContractType,
    JobOffer,
    Score,
)
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
            if not self._column_exists(conn, "offers", "url"):
                self._migrate_v2(conn)
            if not self._column_exists(conn, "offers", "applied"):
                self._migrate_v3(conn)

    @staticmethod
    def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(row[1] == column for row in rows)

    def _migrate_v2(self, conn: sqlite3.Connection) -> None:
        """Migra la tabla antigua añadiendo campos completos de la oferta."""
        conn.execute("""
            CREATE TABLE offers_new (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                currency TEXT,
                compensation_period TEXT,
                contract_type TEXT,
                is_remote INTEGER,
                stack_tags TEXT,
                url TEXT,
                score TEXT NOT NULL,
                reason TEXT,
                missing_skills TEXT,
                matched_skills TEXT,
                draft_content TEXT,
                processed_at_utc TEXT NOT NULL,
                processed_date_local TEXT NOT NULL
            )
        """)
        old_rows = conn.execute(
            "SELECT id, title, company, score, processed_at_utc, processed_date_local FROM offers"
        ).fetchall()
        for row in old_rows:
            conn.execute(
                """
                INSERT INTO offers_new
                (id, title, company, score, processed_at_utc, processed_date_local)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                row,
            )
        conn.execute("DROP TABLE offers")
        conn.execute("ALTER TABLE offers_new RENAME TO offers")

    def _migrate_v3(self, conn: sqlite3.Connection) -> None:
        """Agrega columnas de gestión manual desde el dashboard."""
        conn.execute("ALTER TABLE offers ADD COLUMN applied INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE offers ADD COLUMN notes TEXT DEFAULT ''")

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
                (id, title, company, location, description, salary_min, salary_max,
                 currency, compensation_period, contract_type, is_remote, stack_tags,
                 url, score, reason, missing_skills, matched_skills, draft_content,
                 processed_at_utc, processed_date_local)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    offer.id,
                    offer.title,
                    offer.company,
                    offer.location,
                    offer.description,
                    offer.salary_min,
                    offer.salary_max,
                    offer.currency,
                    offer.compensation_period.value,
                    offer.contract_type.value,
                    int(offer.is_remote),
                    ",".join(offer.stack_tags),
                    offer.url,
                    offer.score.value,
                    offer.reason,
                    ",".join(offer.missing_skills),
                    ",".join(offer.matched_skills),
                    None,
                    processed_at.isoformat(),
                    date_local.isoformat(),
                ),
            )

    def save_draft(self, offer_id: str, draft_content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE offers SET draft_content = ? WHERE id = ?",
                (draft_content, offer_id),
            )

    def find_all_offers(self, days: int | None = None) -> List[Tuple[JobOffer, str | None]]:
        """Devuelve todas las ofertas como entidades; útil para reportes estáticos."""
        sql = """
            SELECT id, title, company, location, description, salary_min, salary_max,
                   currency, compensation_period, contract_type, is_remote, stack_tags,
                   url, score, reason, missing_skills, matched_skills, draft_content
            FROM offers
        """
        params: Tuple = ()
        if days is not None and days > 0:
            cutoff = (
                datetime.now(ZoneInfo(self.timezone)) - timedelta(days=days)
            ).date().isoformat()
            sql += " WHERE processed_date_local >= ?"
            params = (cutoff,)
        sql += " ORDER BY processed_at_utc DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_offer(row) for row in rows]

    def find_all(self, days: int | None = None) -> List[dict]:
        """Devuelve todas las ofertas para el dashboard; filtro por días opcional."""
        sql = """
            SELECT id, title, company, location, description, salary_min, salary_max,
                   currency, compensation_period, contract_type, is_remote, stack_tags,
                   url, score, reason, missing_skills, matched_skills, draft_content,
                   processed_at_utc, processed_date_local, applied, notes
            FROM offers
        """
        params: Tuple = ()
        if days is not None and days > 0:
            cutoff = (
                datetime.now(ZoneInfo(self.timezone)) - timedelta(days=days)
            ).date().isoformat()
            sql += " WHERE processed_date_local >= ?"
            params = (cutoff,)
        sql += " ORDER BY processed_at_utc DESC"
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def update_applied(self, offer_id: str, applied: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE offers SET applied = ? WHERE id = ?",
                (int(applied), offer_id),
            )

    def update_notes(self, offer_id: str, notes: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE offers SET notes = ? WHERE id = ?",
                (notes, offer_id),
            )

    def find_today(self) -> List[Tuple[JobOffer, str | None]]:
        today = self._today_local()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, company, location, description, salary_min, salary_max,
                       currency, compensation_period, contract_type, is_remote, stack_tags,
                       url, score, reason, missing_skills, matched_skills, draft_content
                FROM offers
                WHERE processed_date_local = ?
                ORDER BY processed_at_utc
                """,
                (today.isoformat(),),
            ).fetchall()
        return [self._row_to_offer(row) for row in rows]

    @staticmethod
    def _row_to_offer(row: sqlite3.Row) -> Tuple[JobOffer, str | None]:
        (
            id_,
            title,
            company,
            location,
            description,
            salary_min,
            salary_max,
            currency,
            compensation_period,
            contract_type,
            is_remote,
            stack_tags,
            url,
            score,
            reason,
            missing_skills,
            matched_skills,
            draft_content,
        ) = row
        offer = JobOffer(
            id=id_,
            title=title or "",
            company=company or "",
            location=location or "",
            description=description or "",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency or "USD",
            compensation_period=CompensationPeriod(compensation_period or "monthly"),
            contract_type=ContractType(contract_type or "unknown"),
            is_remote=bool(is_remote),
            stack_tags=[t for t in (stack_tags or "").split(",") if t],
            url=url or "",
            score=Score(score or "red"),
            reason=reason or "",
            missing_skills=[s for s in (missing_skills or "").split(",") if s],
            matched_skills=[s for s in (matched_skills or "").split(",") if s],
        )
        return offer, draft_content

    def _today_local(self) -> date:
        return datetime.now(ZoneInfo(self.timezone)).date()
