def test_global_preferences_and_local_first_routing(client):
    preferences = client.put(
        "/api/v1/global/preferences",
        json={
            "locale": "en-US",
            "region": "US",
            "timezone": "America/Chicago",
            "currency": "USD",
            "measurement_system": "imperial",
            "regional_job_rules": {"work_authorization_questions": True},
        },
    )
    assert preferences.status_code == 200
    assert preferences.json()["timezone"] == "America/Chicago"

    policy = client.put(
        "/api/v1/global/routing/resume-analysis",
        json={
            "task_type": "resume-analysis",
            "local_first": True,
            "allow_cloud_fallback": False,
            "preferred_provider": "ollama",
            "preferred_model": "qwen3:8b",
            "privacy_class": "restricted",
        },
    )
    assert policy.status_code == 200
    decision = client.get(
        "/api/v1/global/routing/resume-analysis/decision?local_available=true"
    )
    assert decision.status_code == 200
    assert decision.json()["provider"] == "ollama"


def test_mobile_endpoint_and_notification_queue(client):
    endpoint = client.post(
        "/api/v1/global/mobile/endpoints",
        json={
            "device_id": "pwa-device-1234",
            "platform": "pwa",
            "locale": "es-MX",
            "timezone": "America/Mexico_City",
            "capabilities": ["offline", "notifications"],
        },
    )
    assert endpoint.status_code == 201
    queued = client.post(
        "/api/v1/global/notifications",
        json={
            "endpoint_id": endpoint.json()["id"],
            "category": "opportunity",
            "title": "New matching job",
            "body": "A high-fit role is ready for review.",
        },
    )
    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
