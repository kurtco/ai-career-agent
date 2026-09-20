import asyncio
import random
from pathlib import Path
from typing import List
from urllib.parse import urljoin, urlparse

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

            await page.goto(search_url, wait_until="domcontentloaded")
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
            await page.goto(url, wait_until="domcontentloaded")
            await self._assert_not_blocked(page)
            await self._human_delay()
            await self._organic_scroll(page)

            job_id = self._extract_job_id(url)
            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else ""
            company_el = await page.query_selector(".top-card-layout__card a")
            company = await company_el.inner_text() if company_el else ""
            location_el = await page.query_selector(".topcard__flavor-row span")
            location = await location_el.inner_text() if location_el else ""
            description_el = await page.query_selector(".description__text")
            description = await description_el.inner_text() if description_el else ""

            return JobOffer(
                id=job_id,
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                description=description.strip(),
                url=url,
            )
        except Exception:
            return None
        finally:
            await page.close()

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

    async def _organic_scroll(self, page) -> None:
        for _ in range(random.randint(2, 4)):
            await page.mouse.wheel(0, random.randint(300, 700))
            await self._human_delay()

    async def _human_delay(self) -> None:
        await asyncio.sleep(random.uniform(1.5, 4.0))
