from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    @abstractmethod
    def health(self) -> tuple[bool, str]: ...

    @abstractmethod
    def list_models(self) -> list[str]: ...

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...
