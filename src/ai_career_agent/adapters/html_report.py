import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from jinja2 import Template

from ai_career_agent.domain.entities import JobOffer, MessageDraft


class HtmlReportGenerator:
    """Genera un reporte HTML al finalizar la corrida; como un presenter visual."""

    def __init__(self, output_dir: Path, auto_open: bool = True):
        self.output_dir = output_dir
        self.auto_open = auto_open
        self._entries: List[Tuple[JobOffer, MessageDraft | None]] = []
        self._template = self._load_template()

    def add(self, offer: JobOffer, draft: MessageDraft | None) -> None:
        self._entries.append((offer, draft))

    def generate(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        report_path = self.output_dir / f"report_{timestamp}.html"

        green = [(o, d) for o, d in self._entries if o.score.value == "green"]
        orange = [(o, d) for o, d in self._entries if o.score.value == "orange"]
        red = [(o, d) for o, d in self._entries if o.score.value == "red"]

        html = self._template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            green_count=len(green),
            orange_count=len(orange),
            red_count=len(red),
            total=len(self._entries),
            green_offers=green,
            orange_offers=orange,
            red_offers=red,
        )

        report_path.write_text(html, encoding="utf-8")
        if self.auto_open:
            webbrowser.open(f"file://{report_path.resolve()}")
        return report_path

    def _load_template(self) -> Template:
        template_path = Path(__file__).with_name("report_template.html")
        return Template(template_path.read_text(encoding="utf-8"))
