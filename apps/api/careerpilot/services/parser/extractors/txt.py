from careerpilot.services.parser.extractors.base import BaseExtractor, ResumeExtractionError


class TxtExtractor(BaseExtractor):
    mime_types = frozenset({"text/plain"})
    extensions = frozenset({".txt"})

    def extract(self, content: bytes) -> str:
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ResumeExtractionError("TXT resumes must use UTF-8 encoding") from error
