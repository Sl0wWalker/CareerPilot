from io import BytesIO

from pypdf import PdfReader

from careerpilot.services.parser.extractors.base import BaseExtractor, ResumeExtractionError


class PdfExtractor(BaseExtractor):
    mime_types = frozenset({"application/pdf"})
    extensions = frozenset({".pdf"})

    def extract(self, content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as error:
            raise ResumeExtractionError("The PDF could not be read") from error
