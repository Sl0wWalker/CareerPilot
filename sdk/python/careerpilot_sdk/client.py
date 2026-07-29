from typing import Any

import httpx


class CareerPilotClient:
    """Synchronous client for CareerPilot's versioned public API."""

    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:8000") -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-API-Key": api_key},
            timeout=30,
        )

    def status(self) -> dict[str, Any]:
        response = self._client.get("/api/v1/platform/public/status")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CareerPilotClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

