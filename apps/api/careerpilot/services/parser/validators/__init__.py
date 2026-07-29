from datetime import date

from careerpilot.services.parser.models import ExtractedFact


class FactValidator:
    def validate(self, facts: list[ExtractedFact]) -> list[str]:
        warnings: list[str] = []
        self._duplicates(facts, "skill", "name", "Duplicate skill", warnings)
        self._duplicates(facts, "experience", "company", "Duplicate company", warnings)
        self._malformed(facts, warnings)
        self._overlaps(facts, warnings)
        return warnings

    @staticmethod
    def _duplicates(
        facts: list[ExtractedFact],
        entity_type: str,
        key: str,
        label: str,
        warnings: list[str],
    ) -> None:
        seen: set[str] = set()
        for fact in facts:
            if fact.entity_type != entity_type:
                continue
            value = str(fact.payload.get(key, "")).strip().casefold()
            if value and value in seen:
                warnings.append(f"{label}: {fact.payload.get(key)}")
            seen.add(value)

    @staticmethod
    def _malformed(facts: list[ExtractedFact], warnings: list[str]) -> None:
        for fact in facts:
            if fact.entity_type == "experience":
                if not fact.payload.get("company") or not fact.payload.get("title"):
                    warnings.append(f"Malformed experience at {fact.source_reference}")
            if fact.entity_type == "education":
                if not fact.payload.get("institution") or not fact.payload.get("degree"):
                    warnings.append(f"Malformed education at {fact.source_reference}")

    @staticmethod
    def _overlaps(facts: list[ExtractedFact], warnings: list[str]) -> None:
        periods: list[tuple[date, date, str]] = []
        for fact in facts:
            if fact.entity_type != "experience":
                continue
            try:
                start = date.fromisoformat(str(fact.payload["start_date"]))
                end_value = fact.payload.get("end_date")
                end = date.fromisoformat(str(end_value)) if end_value else date.max
            except (KeyError, TypeError, ValueError):
                continue
            for existing_start, existing_end, company in periods:
                if start <= existing_end and existing_start <= end:
                    warnings.append(
                        f"Overlapping employment dates: {company} and {fact.payload['company']}"
                    )
            periods.append((start, end, str(fact.payload["company"])))
