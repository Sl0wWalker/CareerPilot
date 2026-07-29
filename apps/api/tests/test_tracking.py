from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from careerpilot.models.tracking import Application
from careerpilot.services.tracking import TrackingService


class MemoryRepository:
    def __init__(self) -> None:
        self.events = []

    def save(self, value):
        return value

    def event(self, application, event_type, title, **details):
        self.events.append((event_type, title, details))


def test_tracking_analytics_and_status_timestamps() -> None:
    repository = MemoryRepository()
    service = TrackingService(repository)
    application = Application(
        profile_id=uuid4(), job_id=uuid4(), status="submitted", source="manual", tags=[]
    )
    application.applied_at = datetime.now(UTC) - timedelta(days=2)
    service.update(application, {"status": "interview"})
    assert application.responded_at is not None
    metrics = service.analytics([application])
    assert metrics["response_rate"] == 100.0
    assert metrics["interview_rate"] == 100.0
    assert repository.events[-1][0] == "status_changed"


def test_application_workflow_api(client: TestClient, monkeypatch) -> None:
    profile = client.post("/profile", json={"first_name": "Ada", "last_name": "Lovelace"})
    assert profile.status_code == 201

    payload = {"jobs": [{
        "id": 99, "title": "Verification Engineer", "content": "Build verification flows.",
        "location": {"name": "Austin, Texas, United States"},
        "absolute_url": "https://example.test/jobs/99",
    }]}

    def fake_get(*args, **kwargs):
        return httpx.Response(200, json=payload, request=httpx.Request("GET", str(args[0])))

    monkeypatch.setattr(httpx, "get", fake_get)
    source = client.post("/jobs/sources", json={
        "provider": "greenhouse", "external_key": "tracking", "name": "Tracking Co",
    }).json()
    client.post(f"/jobs/sources/{source['id']}/sync")
    job_id = client.post("/jobs/search", json={"query": "verification"}).json()[0]["id"]

    created = client.post("/applications", json={"job_id": job_id, "tags": ["priority"]})
    assert created.status_code == 200
    application_id = created.json()["id"]

    moved = client.patch(f"/applications/{application_id}", json={"status": "submitted"})
    assert moved.status_code == 200
    assert moved.json()["applied_at"] is not None

    note = client.post(
        f"/applications/{application_id}/notes", json={"body": "Follow up next week"}
    )
    assert note.status_code == 200
    assert client.get(f"/applications/{application_id}/timeline").json()

    analytics = client.get("/applications/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["submitted"] == 1
    assert client.get("/applications/export").json()["version"] == 1
