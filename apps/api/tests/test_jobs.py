import httpx
from fastapi.testclient import TestClient

from careerpilot.services.jobs.normalization import (
    classify_workplace,
    job_fingerprint,
    normalize_location,
    normalize_salary,
    plain_text,
)


def test_job_normalization_is_stable() -> None:
    assert plain_text("<p>Build&nbsp;systems</p>") == "Build systems"
    assert normalize_location("Austin, Texas, United States") == (
        "Austin",
        "Texas",
        "United States",
    )
    assert classify_workplace("Engineer", "Hybrid schedule", "Austin, TX") == "hybrid"
    assert normalize_salary({"salary_min": 100000, "salary_max": 140000}) == (
        100000,
        140000,
        "USD",
        "year",
    )
    assert job_fingerprint("Acme", "Engineer", "Austin", "Build things") == job_fingerprint(
        " acme ", "ENGINEER", "austin", "Build things"
    )


def test_sources_searches_and_schedules(client: TestClient) -> None:
    source = client.post(
        "/jobs/sources",
        json={
            "provider": "greenhouse",
            "external_key": "example",
            "name": "Example",
        },
    )
    assert source.status_code == 201
    assert client.get("/jobs/sources").json()[0]["provider"] == "greenhouse"

    search = client.post(
        "/jobs/saved-searches",
        json={
            "name": "Formal verification",
            "query": "formal verification",
            "filters": {"workplace_type": "hybrid"},
        },
    )
    assert search.status_code == 201
    saved_id = search.json()["id"]
    schedule = client.post(
        "/jobs/scheduled-searches",
        json={"saved_search_id": saved_id, "cadence": "daily", "enabled": True},
    )
    assert schedule.status_code == 201
    assert client.get("/jobs/scheduled-searches").json()[0]["cadence"] == "daily"

    results = client.post("/jobs/search", json={"query": "python"})
    assert results.status_code == 200
    assert results.json() == []


def test_greenhouse_sync_normalizes_and_deduplicates(
    client: TestClient, monkeypatch
) -> None:
    payload = {
        "jobs": [
            {
                "id": 42,
                "title": "Formal Verification Engineer",
                "content": "<p>Build hybrid verification flows using Python.</p>",
                "location": {"name": "Austin, Texas, United States"},
                "absolute_url": "https://example.test/jobs/42",
                "updated_at": "2026-07-28T10:00:00Z",
            }
        ]
    }

    def fake_get(*args, **kwargs):
        return httpx.Response(200, json=payload, request=httpx.Request("GET", str(args[0])))

    monkeypatch.setattr(httpx, "get", fake_get)
    source = client.post(
        "/jobs/sources",
        json={"provider": "greenhouse", "external_key": "acme", "name": "Acme"},
    ).json()
    first = client.post(f"/jobs/sources/{source['id']}/sync")
    assert first.status_code == 200
    assert first.json()["created"] == 1

    second = client.post(f"/jobs/sources/{source['id']}/sync")
    assert second.status_code == 200
    assert second.json()["updated"] == 1

    jobs = client.post("/jobs/search", json={"query": "Python"}).json()
    assert len(jobs) == 1
    assert jobs[0]["workplace_type"] == "hybrid"
    assert jobs[0]["city"] == "Austin"
