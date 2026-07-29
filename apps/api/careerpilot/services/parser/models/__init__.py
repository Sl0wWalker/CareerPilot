from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExtractedFact:
    entity_type: str
    payload: dict[str, Any]
    confidence: float
    source_reference: str


@dataclass(frozen=True)
class ParseResult:
    raw_text: str
    facts: list[ExtractedFact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
