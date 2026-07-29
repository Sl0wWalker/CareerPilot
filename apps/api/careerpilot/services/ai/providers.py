import json
from typing import Any

import httpx

from careerpilot.services.ai.provider import AIProvider


class OllamaProvider(AIProvider):
    def __init__(
        self, base_url: str, model: str, embedding_model: str, timeout: float = 60
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout

    def health(self) -> tuple[bool, str]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True, "Ollama is available"
        except httpx.HTTPError as error:
            return False, str(error)

    def list_models(self) -> list[str]:
        response = httpx.get(f"{self.base_url}/api/tags", timeout=self.timeout)
        response.raise_for_status()
        return [item["name"] for item in response.json().get("models", [])]

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": schema,
                "stream": False,
                "think": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        value = response.json()["response"]
        return json.loads(value) if isinstance(value, str) else value

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.base_url}/api/embed",
            json={"model": self.embedding_model, "input": texts},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["embeddings"]


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self, base_url: str, api_key: str, model: str, embedding_model: str, timeout: float = 60
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout

    def health(self) -> tuple[bool, str]:
        try:
            response = httpx.get(
                f"{self.base_url}/models", headers=self.headers, timeout=5
            )
            response.raise_for_status()
            return True, "OpenAI-compatible provider is available"
        except httpx.HTTPError as error:
            return False, str(error)

    def list_models(self) -> list[str]:
        response = httpx.get(
            f"{self.base_url}/models", headers=self.headers, timeout=self.timeout
        )
        response.raise_for_status()
        return [item["id"] for item in response.json().get("data", [])]

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return json.loads(response.json()["choices"][0]["message"]["content"])

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers=self.headers,
            json={"model": self.embedding_model, "input": texts},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str, embedding_model: str, timeout: float = 60):
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def health(self) -> tuple[bool, str]:
        try:
            self.list_models()
            return True, "Gemini is available"
        except httpx.HTTPError as error:
            return False, str(error)

    def list_models(self) -> list[str]:
        response = httpx.get(
            f"{self.base_url}/models", params={"key": self.api_key}, timeout=self.timeout
        )
        response.raise_for_status()
        return [item["name"] for item in response.json().get("models", [])]

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseJsonSchema": schema,
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return json.loads(response.json()["candidates"][0]["content"]["parts"][0]["text"])

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            response = httpx.post(
                f"{self.base_url}/models/{self.embedding_model}:embedContent",
                params={"key": self.api_key},
                json={"content": {"parts": [{"text": text}]}},
                timeout=self.timeout,
            )
            response.raise_for_status()
            vectors.append(response.json()["embedding"]["values"])
        return vectors
