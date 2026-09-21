import csv
import re
from pathlib import Path
from typing import List


class LinkedInJobAlertsParser:
    """Lee Job Alerts.csv del export de LinkedIn; como un adapter de infraestructura."""

    def __init__(self, export_path: Path):
        self.export_path = export_path

    def find_job_alerts_file(self) -> Path | None:
        if not self.export_path.exists():
            return None
        for candidate in self.export_path.iterdir():
            if candidate.is_file() and re.match(
                r"job alerts?\.csv", candidate.name, re.IGNORECASE
            ):
                return candidate
        return None

    def parse_search_urls(self) -> List[str]:
        file_path = self.find_job_alerts_file()
        if not file_path:
            return []

        with file_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []

            url_column = self._find_url_column(reader.fieldnames)
            if not url_column:
                return []

            urls: set[str] = set()
            for row in reader:
                value = (row.get(url_column) or "").strip()
                if self._is_linkedin_search_url(value):
                    urls.add(value)
            return sorted(urls)

    @staticmethod
    def _find_url_column(fieldnames: List[str]) -> str | None:
        for name in fieldnames:
            lower = name.lower()
            if "url" in lower or "search" in lower or "link" in lower:
                return name
        return None

    @staticmethod
    def _is_linkedin_search_url(value: str) -> bool:
        return value.startswith("https://www.linkedin.com/jobs/search")
