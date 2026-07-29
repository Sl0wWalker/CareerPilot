import asyncio

from careerpilot.services.platform import EventBus, PlatformEvent


def test_api_key_lifecycle_and_public_authentication(client):
    created = client.post(
        "/api/v1/platform/keys",
        json={"name": "Integration test", "scopes": ["platform:read"]},
    )
    assert created.status_code == 201
    secret = created.json()["secret"]
    assert secret.startswith("cp_")

    keys = client.get("/api/v1/platform/keys")
    assert keys.status_code == 200
    assert keys.json()[0]["name"] == "Integration test"
    assert "secret" not in keys.json()[0]

    assert client.get("/api/v1/platform/public/status").status_code == 401
    response = client.get(
        "/api/v1/platform/public/status", headers={"X-API-Key": secret}
    )
    assert response.status_code == 200
    assert response.json()["api_version"] == "v1"

    revoked = client.delete(f"/api/v1/platform/keys/{created.json()['id']}")
    assert revoked.status_code == 204
    assert (
        client.get(
            "/api/v1/platform/public/status", headers={"X-API-Key": secret}
        ).status_code
        == 401
    )


def test_webhooks_and_overview(client):
    created = client.post(
        "/api/v1/platform/webhooks",
        json={
            "url": "https://example.test/careerpilot",
            "event_types": ["application.submitted"],
            "description": "Test receiver",
        },
    )
    assert created.status_code == 201
    assert client.get("/api/v1/platform/webhooks").json()[0]["enabled"] is True
    overview = client.get("/api/v1/platform/overview")
    assert overview.status_code == 200
    assert overview.json()["webhooks"] == 1
    assert "ai_provider" in overview.json()["extension_types"]


def test_event_bus_delivers_to_handlers():
    bus = EventBus()
    received: list[PlatformEvent] = []

    async def handler(event: PlatformEvent):
        received.append(event)

    async def exercise():
        unsubscribe = bus.subscribe("test.created", handler)
        await bus.publish(PlatformEvent("test.created", {"id": "1"}))
        unsubscribe()
        await bus.publish(PlatformEvent("test.created", {"id": "2"}))

    asyncio.run(exercise())
    assert received == [PlatformEvent("test.created", {"id": "1"})]
