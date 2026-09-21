import asyncio
import random
import re
from pathlib import Path
from typing import List
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from ai_career_agent.domain.entities import ContractType, JobOffer
from ai_career_agent.domain.exceptions import BlockedError
from ai_career_agent.domain.ports import JobScraper


class PlaywrightLinkedInScraper(JobScraper):
    """Scraper de LinkedIn con comportamiento humano; adaptador de infraestructura."""

    def __init__(self, session_state_path: Path):
        self.session_state_path = session_state_path

    async def fetch(self, search_url: str, max_offers: int) -> List[JobOffer]:
        if not self.session_state_path.exists():
            raise FileNotFoundError(
                f"No existe {self.session_state_path}. "
                "Ejecuta primero 'uv run python scripts/create_session.py' y loguéate manualmente."
            )

        offers: List[JobOffer] = []
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                storage_state=str(self.session_state_path),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            search_url = self._ensure_last_24h(search_url)
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await self._assert_not_blocked(page)
            await self._human_delay()
            await self._organic_scroll(page)

            job_links = await self._collect_job_links(page, max_offers)
            for link in job_links:
                if len(offers) >= max_offers:
                    break
                offer = await self._extract_job_detail(context, link)
                if offer:
                    offers.append(offer)
                await self._human_delay()

            await browser.close()
        return offers

    async def _collect_job_links(self, page, max_offers: int) -> List[str]:
        links: set[str] = set()
        attempts = 0
        while len(links) < max_offers and attempts < 5:
            await self._organic_scroll(page)
            anchors = await page.query_selector_all('a[href*="/jobs/view/"]')
            for anchor in anchors:
                href = await anchor.get_attribute("href")
                if href:
                    links.add(urljoin("https://www.linkedin.com", href))
                if len(links) >= max_offers:
                    break
            attempts += 1
            await self._human_delay()
        return list(links)[:max_offers]

    async def _extract_job_detail(self, context, url: str) -> JobOffer | None:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await self._assert_not_blocked(page)
            await self._human_delay()
            await self._organic_scroll(page)
            await asyncio.sleep(2)  # Espera renderizado JS

            body_text = await page.inner_text("body")
            page_title = await page.title()
            return self._parse_job_detail(url, body_text, page_title)
        except Exception:
            return None
        finally:
            await page.close()

    def _parse_job_detail(self, url: str, body_text: str, page_title: str) -> JobOffer:
        """Extrae campos desde el texto visible; LinkedIn usa clases dinámicas."""
        job_id = self._extract_job_id(url)
        title, company = self._extract_title_and_company(page_title)
        location = self._extract_location(body_text)
        description = self._extract_description(body_text)

        text_lower = body_text.lower()
        is_remote = "remote" in text_lower or "remoto" in text_lower
        contract_type = ContractType.UNKNOWN
        if "full-time" in text_lower or "tiempo completo" in text_lower:
            contract_type = ContractType.FULL_TIME
        elif "part-time" in text_lower or "medio tiempo" in text_lower:
            contract_type = ContractType.PART_TIME
        elif "contract" in text_lower or "contrato" in text_lower:
            contract_type = ContractType.CONTRACT

        return JobOffer(
            id=job_id,
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            is_remote=is_remote,
            contract_type=contract_type,
        )

    @staticmethod
    def _extract_title_and_company(page_title: str) -> tuple[str, str]:
        # Título típico: "Job Title | Company | LinkedIn"
        parts = [p.strip() for p in page_title.split("|")]
        title = parts[0] if parts else ""
        company = parts[-2] if len(parts) >= 3 else ""
        return title, company

    @staticmethod
    def _extract_location(body_text: str) -> str:
        # Línea tipo: "Latin America · 5 days ago · Over 100 people clicked apply"
        match = re.search(r"^([^\n·]+?)\s*·\s*\d+\s+day[s]?\s+ago", body_text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_description(body_text: str) -> str:
        match = re.search(
            r"About the job\s*\n+(.*?)(?:\n+Set alert for similar jobs|\n+\.\.\.)",
            body_text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return re.sub(r"\n{2,}", "\n", match.group(1).strip())
        return ""

    async def _assert_not_blocked(self, page) -> None:
        url = page.url
        title = await page.title()
        if "checkpoint" in url.lower() or "captcha" in title.lower() or "security" in title.lower():
            raise BlockedError(f"LinkedIn bloqueó la sesión: {url}")

    @staticmethod
    def _extract_job_id(url: str) -> str:
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p.isdigit()]
        return parts[0] if parts else url

    @staticmethod
    def _ensure_last_24h(url: str) -> str:
        """Fuerza el filtro de LinkedIn para ofertas de las últimas 24 horas."""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query["f_TPR"] = ["r86400"]
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    async def _organic_scroll(self, page) -> None:
        for _ in range(random.randint(2, 4)):
            await page.mouse.wheel(0, random.randint(300, 700))
            await self._human_delay()

    async def _human_delay(self) -> None:
        await asyncio.sleep(random.uniform(1.5, 4.0))
