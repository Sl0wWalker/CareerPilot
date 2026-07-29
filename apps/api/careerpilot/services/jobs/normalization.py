import re
from hashlib import sha256
from html import unescape
from typing import Any


def plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def normalize_location(value: str | None) -> tuple[str | None, str | None, str | None]:
    if not value:
        return None, None, None
    parts = [item.strip() for item in value.split(",") if item.strip()]
    if len(parts) >= 3:
        return parts[0], parts[-2], parts[-1]
    if len(parts) == 2:
        return parts[0], parts[1], None
    return parts[0], None, None


def classify_workplace(title: str, description: str, location: str | None) -> str:
    text = f"{title} {description} {location or ''}".casefold()
    if "hybrid" in text:
        return "hybrid"
    if any(token in text for token in ("remote", "work from home", "distributed")):
        return "remote"
    if location:
        return "onsite"
    return "unknown"


def normalize_salary(
    payload: dict[str, Any],
) -> tuple[int | None, int | None, str | None, str | None]:
    minimum = payload.get("salary_min")
    maximum = payload.get("salary_max")
    return (
        int(minimum) if minimum is not None else None,
        int(maximum) if maximum is not None else None,
        str(payload.get("salary_currency") or "USD") if minimum or maximum else None,
        str(payload.get("salary_period") or "year") if minimum or maximum else None,
    )


def job_fingerprint(company: str, title: str, location: str | None, description: str) -> str:
    stable = "|".join(
        (
            company.casefold().strip(),
            title.casefold().strip(),
            (location or "").casefold().strip(),
            plain_text(description)[:500].casefold(),
        )
    )
    return sha256(stable.encode()).hexdigest()
