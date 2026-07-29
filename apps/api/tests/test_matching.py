import httpx
from fastapi.testclient import TestClient

from careerpilot.api.ai import get_ai_provider
from careerpilot.main import app
from careerpilot.services.ai import AIProvider


class FakeProvider(AIProvider):
    def health(self) -> tuple[bool, str]:
        return True, "test"

    def list_models(self) -> list[str]:
        return ["test"]

    def generate_json(self, prompt, schema):
        return {}

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0], [0.9, 0.1]]


def test_matching_settings_validate_and_persist(client: TestClient) -> None:
    settings = client.get("/matching/settings")
    assert settings.status_code == 200
    assert round(sum(settings.json()["weights"].values()), 5) == 1

    invalid = client.put(
        "/matching/settings",
        json={
            "weights": {"skills": 1},
            "hard_block_threshold": 0.35,
            "minimum_recommendation_score": 65,
        },
    )
    assert invalid.status_code == 422

    payload = settings.json()
    payload.pop("id")
    payload["minimum_recommendation_score"] = 70
    saved = client.put("/matching/settings", json=payload)
    assert saved.status_code == 200
    assert saved.json()["minimum_recommendation_score"] == 70


def test_explainable_match_uses_verified_profile_and_detects_gaps(
    client: TestClient, monkeypatch
) -> None:
    profile = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "city": "Austin",
        "experiences": [
            {
                "company": "Acme",
                "title": "Senior Verification Engineer",
                "start_date": "2020-01-01",
                "is_current": True,
                "description": "Automated formal verification flows with Python and Tcl.",
            }
        ],
        "education": [{"institution": "University", "degree": "Bachelor of Engineering"}],
        "projects": [{"name": "LEC automation", "description": "Python verification tooling"}],
        "skills": [{"name": "Python"}, {"name": "Tcl"}, {"name": "Conformal"}],
        "job_preference": {
            "target_roles": "Formal Verification Engineer",
            "preferred_locations": "Austin",
            "remote_ok": True,
            "requires_sponsorship": True,
        },
    }
    assert client.post("/profile", json=profile).status_code == 201

    payload = {
        "jobs": [
            {
                "id": 9,
                "title": "Senior Formal Verification Engineer",
                "content": (
                    "<p>Use Python, Tcl, Conformal, SystemVerilog, and Kubernetes. "
                    "This role is in Austin.</p>"
                ),
                "location": {"name": "Austin, Texas, United States"},
                "absolute_url": "https://example.test/jobs/9",
            }
        ]
    }

    def fake_get(*args, **kwargs):
        return httpx.Response(200, json=payload, request=httpx.Request("GET", str(args[0])))

    monkeypatch.setattr(httpx, "get", fake_get)
    source = client.post(
        "/jobs/sources",
        json={"provider": "greenhouse", "external_key": "match-test", "name": "Match Test"},
    ).json()
    assert client.post(f"/jobs/sources/{source['id']}/sync").status_code == 200
    job = client.post("/jobs/search", json={"query": "Formal Verification"}).json()[0]

    app.dependency_overrides[get_ai_provider] = lambda: FakeProvider()
    result = client.post(f"/jobs/{job['id']}/match")
    app.dependency_overrides.pop(get_ai_provider, None)

    assert result.status_code == 200
    body = result.json()
    assert body["overall_score"] > 50
    assert set(body["components"]) == {
        "skills",
        "experience",
        "seniority",
        "education",
        "location",
        "work_authorization",
        "keywords",
        "semantic_similarity",
    }
    assert any("kubernetes" in gap.casefold() for gap in body["gaps"])
    assert body["evidence"]
    assert client.get(f"/jobs/{job['id']}/match").status_code == 200
