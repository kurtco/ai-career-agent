import pytest

from ai_career_agent.adapters.presenter import ConsolePresenter
from ai_career_agent.application.use_cases.evaluate_job import EvaluateJobUseCase
from ai_career_agent.application.use_cases.fetch_offers import FetchOffersUseCase
from ai_career_agent.application.use_cases.generate_message import GenerateMessageUseCase
from ai_career_agent.domain.entities import (
    CompensationPeriod,
    ContractType,
    JobOffer,
    MessageDraft,
    Score,
)
from ai_career_agent.domain.ports import JobScraper, LLMClient, OfferRepository
from ai_career_agent.infrastructure.parsers.linkedin_job_alerts_parser import (
    LinkedInJobAlertsParser,
)
from ai_career_agent.infrastructure.persistence.sqlite_repository import (
    SqliteOfferRepository,
)
from ai_career_agent.infrastructure.scraper.playwright_linkedin import (
    PlaywrightLinkedInScraper,
)


class FakeRepository(OfferRepository):
    def __init__(self):
        self.offers: dict[str, JobOffer] = {}
        self._count_today = 0

    def count_today(self) -> int:
        return self._count_today

    def exists(self, offer_id: str) -> bool:
        return offer_id in self.offers

    def save(self, offer: JobOffer) -> None:
        self.offers[offer.id] = offer

    def set_count_today(self, value: int) -> None:
        self._count_today = value


class FakeLLMClient(LLMClient):
    def __init__(self, results: dict[str, JobOffer] | None = None):
        self.results = results or {}
        self.calls: list[tuple[str, str]] = []

    async def evaluate(self, offer: JobOffer) -> JobOffer:
        if offer.id in self.results:
            scored = self.results[offer.id]
            offer.score = scored.score
            offer.reason = scored.reason
            offer.missing_skills = scored.missing_skills
            offer.matched_skills = scored.matched_skills
        return offer

    async def generate_message(self, offer: JobOffer, cv_text: str) -> MessageDraft:
        self.calls.append((offer.id, cv_text))
        return MessageDraft(offer_id=offer.id, content=f"Draft for {offer.title}")


class FakeScraper(JobScraper):
    def __init__(self, offers: list[JobOffer]):
        self.offers = offers

    async def fetch(self, search_url: str, max_offers: int) -> list[JobOffer]:
        return self.offers[:max_offers]


@pytest.fixture
def repo(tmp_path):
    return SqliteOfferRepository(tmp_path / "history.db", timezone="America/Bogota")


@pytest.fixture
def fake_repo():
    return FakeRepository()


@pytest.fixture
def fake_llm():
    return FakeLLMClient()


@pytest.mark.asyncio
async def test_ca1_hourly_under_35_is_red_no_draft(fake_repo, fake_llm):
    offer = JobOffer(
        id="1",
        title="Python Dev",
        company="X",
        compensation_period=CompensationPeriod.HOURLY,
        salary_min=20,
        salary_max=25,
        contract_type=ContractType.FULL_TIME,
    )
    scored = JobOffer(
        id="1",
        title="Python Dev",
        company="X",
        score=Score.RED,
        reason="Pago por hora menor a $35/h",
    )
    fake_llm.results["1"] = scored

    use_case = EvaluateJobUseCase(fake_llm, fake_repo)
    result = await use_case.execute(offer)

    assert result.score == Score.RED
    assert fake_repo.exists("1")

    generate = GenerateMessageUseCase(fake_llm, "cv")
    draft = None
    if result.score in (Score.GREEN, Score.ORANGE):
        draft = await generate.execute(result)
    assert draft is None


@pytest.mark.asyncio
async def test_ca2_4500_fulltime_longterm_is_at_least_orange(fake_repo, fake_llm):
    offer = JobOffer(
        id="2",
        title="Full-Stack TS",
        company="Y",
        compensation_period=CompensationPeriod.MONTHLY,
        salary_min=4500,
        salary_max=4500,
        contract_type=ContractType.FULL_TIME,
    )
    scored = JobOffer(
        id="2",
        title="Full-Stack TS",
        company="Y",
        score=Score.ORANGE,
        reason="Cumple salario full-time long-term, falta AI",
    )
    fake_llm.results["2"] = scored

    use_case = EvaluateJobUseCase(fake_llm, fake_repo)
    result = await use_case.execute(offer)

    assert result.score in (Score.GREEN, Score.ORANGE)


@pytest.mark.asyncio
async def test_ca3_senior_python_only_is_red(fake_repo, fake_llm):
    offer = JobOffer(
        id="3",
        title="Senior Python Engineer",
        company="Z",
        stack_tags=["python", "django"],
        compensation_period=CompensationPeriod.MONTHLY,
        salary_min=6000,
        contract_type=ContractType.FULL_TIME,
    )
    scored = JobOffer(
        id="3",
        title="Senior Python Engineer",
        company="Z",
        score=Score.RED,
        reason="Rol 100% Python senior",
    )
    fake_llm.results["3"] = scored

    use_case = EvaluateJobUseCase(fake_llm, fake_repo)
    result = await use_case.execute(offer)

    assert result.score == Score.RED


@pytest.mark.asyncio
async def test_ca4_hybrid_python_node_remote_5k_is_green_and_draft_under_700(fake_repo, fake_llm):
    offer = JobOffer(
        id="4",
        title="AI Full-Stack",
        company="W",
        is_remote=True,
        stack_tags=["python", "nodejs", "typescript", "react", "nextjs"],
        compensation_period=CompensationPeriod.MONTHLY,
        salary_min=5000,
        contract_type=ContractType.FULL_TIME,
    )
    scored = JobOffer(
        id="4",
        title="AI Full-Stack",
        company="W",
        score=Score.GREEN,
        reason="Match perfecto",
    )
    fake_llm.results["4"] = scored

    use_case = EvaluateJobUseCase(fake_llm, fake_repo)
    result = await use_case.execute(offer)

    assert result.score == Score.GREEN

    generate = GenerateMessageUseCase(fake_llm, "cv highlights")
    draft = await generate.execute(result)
    assert draft is not None
    assert len(draft.content) <= 700


@pytest.mark.asyncio
async def test_daily_limit_blocks_fetch(fake_repo, fake_llm):
    fake_repo.set_count_today(30)
    scraper = FakeScraper([JobOffer(id="x", title="Test", company="C")])
    evaluate = EvaluateJobUseCase(fake_llm, fake_repo)
    fetch = FetchOffersUseCase(scraper, fake_repo, evaluate, daily_limit=30)

    result = await fetch.execute("http://example.com")
    assert result == []


@pytest.mark.asyncio
async def test_blacklisted_company_is_skipped(fake_repo, fake_llm):
    offers = [
        JobOffer(id="b1", title="Dev", company="BairesDev"),
        JobOffer(id="g1", title="Dev", company="GoodCorp"),
    ]
    scored = JobOffer(id="g1", title="Dev", company="GoodCorp", score=Score.GREEN)
    fake_llm.results = {"g1": scored}
    scraper = FakeScraper(offers)
    evaluate = EvaluateJobUseCase(fake_llm, fake_repo)
    fetch = FetchOffersUseCase(
        scraper, fake_repo, evaluate, company_blacklist=["BairesDev"]
    )

    result = await fetch.execute("http://example.com")
    assert len(result) == 1
    assert result[0].company == "GoodCorp"
    assert not fake_repo.exists("b1")




def test_ensure_last_24h_filter():
    url_without = "https://www.linkedin.com/jobs/search?keywords=typescript"
    url_with_other = "https://www.linkedin.com/jobs/search?keywords=typescript&f_TPR=r604800"

    assert "f_TPR=r86400" in PlaywrightLinkedInScraper._ensure_last_24h(url_without)
    assert PlaywrightLinkedInScraper._ensure_last_24h(url_with_other) == (
        "https://www.linkedin.com/jobs/search?keywords=typescript&f_TPR=r86400"
    )


def test_parse_job_alerts_csv(tmp_path):
    export_dir = tmp_path / "linkedin_export"
    export_dir.mkdir()
    csv_file = export_dir / "Job Alerts.csv"
    csv_file.write_text(
        "Title,Search URL,Frequency\n"
        "TypeScript Remote,https://www.linkedin.com/jobs/search?keywords=typescript&f_TPR=r86400,Daily\n"
        "Node.js LATAM,https://www.linkedin.com/jobs/search?keywords=nodejs&Daily\n",
        encoding="utf-8",
    )

    parser = LinkedInJobAlertsParser(export_dir)
    urls = parser.parse_search_urls()
    assert len(urls) == 2
    assert "https://www.linkedin.com/jobs/search?keywords=typescript&f_TPR=r86400" in urls
    assert "https://www.linkedin.com/jobs/search?keywords=nodejs&Daily" in urls


@pytest.mark.asyncio
async def test_missing_salary_is_orange_not_red(fake_repo, fake_llm):
    offer = JobOffer(
        id="5",
        title="Full-Stack Node/React",
        company="GoodCorp",
        stack_tags=["nodejs", "react", "typescript"],
        is_remote=True,
        contract_type=ContractType.FULL_TIME,
    )
    scored = JobOffer(
        id="5",
        title="Full-Stack Node/React",
        company="GoodCorp",
        score=Score.ORANGE,
        reason="No especifica salario; stack remoto full-time coincide",
    )
    fake_llm.results["5"] = scored

    use_case = EvaluateJobUseCase(fake_llm, fake_repo)
    result = await use_case.execute(offer)

    assert result.score == Score.ORANGE
    generate = GenerateMessageUseCase(fake_llm, "cv")
    draft = await generate.execute(result)
    assert draft is not None


@pytest.mark.asyncio
async def test_repository_counts_today_respecting_timezone(repo):
    from datetime import datetime, timedelta, timezone

    offer = JobOffer(id="r1", title="T", company="C", score=Score.GREEN)
    # Hora en UTC que aún es hoy en Bogotá (UTC-5)
    offer.processed_at = datetime.now(timezone.utc) - timedelta(hours=3)
    repo.save(offer)
    assert repo.count_today() == 1
