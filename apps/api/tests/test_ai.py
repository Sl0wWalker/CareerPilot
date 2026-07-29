from typing import Any

from fastapi.testclient import TestClient

from careerpilot.api.ai import get_ai_provider
from careerpilot.main import app
from careerpilot.services.ai import AIProvider


class FakeProvider(AIProvider):
    def health(self) -> tuple[bool, str]:
        return True, "fake provider ready"

    def list_models(self) -> list[str]:
        return ["fake-model"]

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if "summarizing" in prompt:
            return {
                "short": "Engineer focused on Python.",
                "medium": "Engineer with verified Python experience.",
                "linkedin": "I build reliable Python systems.",
            }
        return {
            "suggestions": [
                {
                    "type": "add_skill",
                    "source_type": "experience",
                    "source_id": None,
                    "original": None,
                    "proposed": {"name": "FastAPI"},
                    "rationale": "Explicitly evidenced in the profile.",
                    "confidence": 0.91,
                }
            ]
        }

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]


def create_profile(client: TestClient) -> None:
    response = client.post(
        "/profile",
        json={
            "first_name": "Test",
            "last_name": "Candidate",
            "skills": [{"name": "Python", "years_experience": 3}],
            "experiences": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "start_date": "2023-01-01",
                    "is_current": True,
                    "description": "Built FastAPI services.",
                }
            ],
        },
    )
    assert response.status_code == 201


def test_ai_health_settings_and_summary(client: TestClient) -> None:
    app.dependency_overrides[get_ai_provider] = lambda: FakeProvider()
    create_profile(client)

    health = client.get("/ai/health")
    assert health.status_code == 200
    assert health.json()["available"] is True

    settings = client.get("/ai/settings")
    assert settings.status_code == 200
    assert settings.json()["provider"] == "ollama"

    summary = client.post("/ai/profile/summarize")
    assert summary.status_code == 200
    assert "Python" in summary.json()["short"]


def test_suggestion_approval_and_semantic_search(client: TestClient) -> None:
    app.dependency_overrides[get_ai_provider] = lambda: FakeProvider()
    create_profile(client)

    enrichment = client.post("/ai/profile/enrich")
    assert enrichment.status_code == 200
    suggestion = enrichment.json()[0]
    assert suggestion["status"] == "pending"

    approval = client.patch(
        f"/ai/suggestions/{suggestion['id']}", json={"status": "approved"}
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"
    skills = client.get("/profile").json()["skills"]
    assert any(item["name"] == "FastAPI" for item in skills)

    search = client.post("/ai/profile/search", json={"query": "Python systems", "limit": 3})
    assert search.status_code == 200
    assert search.json()
