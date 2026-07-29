from careerpilot.services.parser.cleaners import TextCleaner
from careerpilot.services.parser.detectors import SectionDetector
from careerpilot.services.parser.extractors import (
    BaseExtractor,
    DocxExtractor,
    PdfExtractor,
    TxtExtractor,
    UnsupportedResumeTypeError,
)
from careerpilot.services.parser.models import ParseResult
from careerpilot.services.parser.parsers import EntityParser
from careerpilot.services.parser.validators import FactValidator


class ResumeParserPipeline:
    parser_version = "deterministic-1"

    def __init__(
        self,
        extractors: list[BaseExtractor] | None = None,
        cleaner: TextCleaner | None = None,
        detector: SectionDetector | None = None,
        parser: EntityParser | None = None,
        validator: FactValidator | None = None,
    ) -> None:
        self.extractors = extractors or [PdfExtractor(), DocxExtractor(), TxtExtractor()]
        self.cleaner = cleaner or TextCleaner()
        self.detector = detector or SectionDetector()
        self.parser = parser or EntityParser()
        self.validator = validator or FactValidator()

    def run(self, filename: str, mime_type: str, content: bytes) -> ParseResult:
        extractor = next(
            (candidate for candidate in self.extractors if candidate.supports(filename, mime_type)),
            None,
        )
        if extractor is None:
            raise UnsupportedResumeTypeError("Only PDF, DOCX, and UTF-8 TXT files are supported")
        raw_text = self.cleaner.clean(extractor.extract(content))
        if not raw_text:
            raise ValueError("No readable text was found in the resume")
        facts = self.parser.parse(self.detector.detect(raw_text))
        return ParseResult(raw_text=raw_text, facts=facts, warnings=self.validator.validate(facts))
