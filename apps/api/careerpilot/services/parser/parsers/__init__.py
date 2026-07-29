import re
from datetime import date

from careerpilot.services.parser.models import ExtractedFact

DATE_RANGE = re.compile(
    r"(?P<start>(?:19|20)\d{2})(?:\s*[-–—]\s*)(?P<end>(?:19|20)\d{2}|present|current)",
    re.IGNORECASE,
)
BULLET = re.compile(r"^[•●▪◦*\-–—]\s*")


def source(section: str, index: int) -> str:
    return f"{section}:line:{index + 1}"


class EntityParser:
    def parse(self, sections: dict[str, list[str]]) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []
        facts.extend(self._skills(sections.get("skills", [])))
        facts.extend(self._structured_lines("experience", sections.get("experience", [])))
        facts.extend(self._structured_lines("education", sections.get("education", [])))
        facts.extend(self._simple("project", sections.get("projects", [])))
        facts.extend(self._simple("certification", sections.get("certifications", [])))
        facts.extend(self._simple("achievement", sections.get("awards", [])))
        return facts

    def _skills(self, lines: list[str]) -> list[ExtractedFact]:
        values: list[tuple[str, int]] = []
        for index, line in enumerate(lines):
            for value in re.split(r"[,;|]", BULLET.sub("", line)):
                skill = value.strip()
                if skill:
                    values.append((skill, index))
        return [
            ExtractedFact("skill", {"name": skill}, 0.9, source("skills", index))
            for skill, index in values
        ]

    def _structured_lines(self, kind: str, lines: list[str]) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []
        for index, line in enumerate(lines):
            clean = BULLET.sub("", line).strip()
            if not clean:
                continue
            date_match = DATE_RANGE.search(clean)
            parts = [part.strip() for part in re.split(r"\s+[|·]\s+|\s{2,}", clean) if part.strip()]
            if kind == "experience" and len(parts) >= 2:
                payload = {
                    "title": parts[0],
                    "company": parts[1],
                    "start_date": self._date(date_match, "start"),
                    "end_date": self._date(date_match, "end"),
                    "is_current": bool(
                        date_match and date_match.group("end").lower() in {"present", "current"}
                    ),
                    "description": clean,
                }
            elif kind == "education" and len(parts) >= 2:
                payload = {
                    "degree": parts[0],
                    "institution": parts[1],
                    "start_year": self._year(date_match, "start"),
                    "end_year": self._year(date_match, "end"),
                }
            else:
                continue
            facts.append(ExtractedFact(kind, payload, 0.72, source(kind, index)))
        return facts

    def _simple(self, kind: str, lines: list[str]) -> list[ExtractedFact]:
        facts = []
        for index, line in enumerate(lines):
            clean = BULLET.sub("", line).strip()
            if not clean:
                continue
            if kind == "project":
                payload = {"name": clean[:200], "description": clean}
            elif kind == "certification":
                payload = {"name": clean[:200]}
            else:
                payload = {"title": clean[:200], "description": clean}
            facts.append(ExtractedFact(kind, payload, 0.65, source(kind, index)))
        return facts

    @staticmethod
    def _year(match: re.Match[str] | None, group: str) -> int | None:
        if not match:
            return None
        value = match.group(group)
        return int(value) if value.isdigit() else None

    def _date(self, match: re.Match[str] | None, group: str) -> str | None:
        year = self._year(match, group)
        return date(year, 1, 1).isoformat() if year else None
