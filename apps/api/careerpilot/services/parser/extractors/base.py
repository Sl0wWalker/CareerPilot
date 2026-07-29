from abc import ABC, abstractmethod


class UnsupportedResumeTypeError(ValueError):
    pass


class ResumeExtractionError(ValueError):
    pass


class BaseExtractor(ABC):
    mime_types: frozenset[str]
    extensions: frozenset[str]

    def supports(self, filename: str, mime_type: str) -> bool:
        extension = "." + filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
        return mime_type.lower() in self.mime_types and extension in self.extensions

    @abstractmethod
    def extract(self, content: bytes) -> str:
        raise NotImplementedError
