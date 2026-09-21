from ai_career_agent.adapters.html_report import HtmlReportGenerator
from ai_career_agent.domain.entities import JobOffer, MessageDraft, Score


def test_html_report_contains_offers_and_copy_buttons(tmp_path):
    report = HtmlReportGenerator(tmp_path, auto_open=False)

    green = JobOffer(
        id="g1",
        title="Senior Full-Stack",
        company="GoodCorp",
        score=Score.GREEN,
        reason="Match perfecto",
        url="https://www.linkedin.com/jobs/view/1/",
    )
    orange = JobOffer(
        id="o1",
        title="Frontend Dev",
        company="OtherCorp",
        score=Score.ORANGE,
        reason="Falta salario",
        url="https://www.linkedin.com/jobs/view/2/",
    )
    red = JobOffer(
        id="r1",
        title="Python Dev",
        company="BadCorp",
        score=Score.RED,
        reason="Stack no coincide",
        url="https://www.linkedin.com/jobs/view/3/",
    )

    report.add(green, MessageDraft(offer_id="g1", content="Hi GoodCorp team..."))
    report.add(orange, None)
    report.add(red, None)

    path = report.generate()

    html = path.read_text(encoding="utf-8")
    assert "GoodCorp" in html
    assert "OtherCorp" in html
    assert "BadCorp" in html
    assert "Hi GoodCorp team..." in html
    assert "Copiar mensaje" in html
    assert "Copiar título + link" in html
    assert "Copiar link" in html
    assert "offer-g1" in html
    assert "offer-o1" in html
    assert "offer-r1" in html
