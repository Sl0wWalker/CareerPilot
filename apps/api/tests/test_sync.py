def register_device(client, key="laptop"):
    response = client.post(
        "/api/v1/sync/devices",
        json={"device_key": key, "display_name": key.title(), "platform": "Windows"},
    )
    assert response.status_code == 201
    return response.json()


def test_device_registration_and_incremental_sync(client):
    device = register_device(client)
    pushed = client.post(
        "/api/v1/sync/push",
        json={
            "device_id": device["id"],
            "changes": [
                {
                    "entity_type": "settings",
                    "entity_key": "preferences",
                    "base_revision": 0,
                    "payload": {"theme": "system"},
                }
            ],
        },
    )
    assert pushed.status_code == 200
    assert pushed.json()["accepted"][0]["revision"] == 1
    pulled = client.get("/api/v1/sync/pull?cursor=0")
    assert pulled.status_code == 200
    assert pulled.json()["cursor"] == 1
    assert pulled.json()["accepted"][0]["payload_json"] == {"theme": "system"}


def test_conflicting_device_changes_require_resolution(client):
    first = register_device(client, "first")
    second = register_device(client, "second")
    payload = {
        "entity_type": "profile",
        "entity_key": "primary",
        "base_revision": 0,
        "payload": {"name": "First"},
    }
    assert client.post(
        "/api/v1/sync/push", json={"device_id": first["id"], "changes": [payload]}
    ).status_code == 200
    result = client.post(
        "/api/v1/sync/push",
        json={
            "device_id": second["id"],
            "changes": [{**payload, "payload": {"name": "Second"}}],
        },
    )
    conflict_id = result.json()["conflicts"][0]
    resolved = client.post(
        f"/api/v1/sync/conflicts/{conflict_id}/resolve",
        json={"resolution": "keep_local"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_connected_accounts_are_permission_scoped(client):
    providers = client.get("/api/v1/sync/integrations")
    assert providers.status_code == 200
    assert {item["provider"] for item in providers.json()} >= {"gmail", "google_drive", "linkedin"}
    account = client.post(
        "/api/v1/sync/accounts",
        json={
            "provider": "gmail",
            "external_account_id": "candidate@example.test",
            "display_name": "Career inbox",
            "scopes": ["job-alert import"],
        },
    )
    assert account.status_code == 201
    assert account.json()["status"] == "pending"
    assert "credential_reference" not in account.json()


def test_workspace_members_use_granular_permissions(client):
    workspace = client.post(
        "/api/v1/sync/workspaces",
        json={"name": "Resume review", "description": "Share selected artifacts"},
    )
    assert workspace.status_code == 201
    member = client.post(
        f"/api/v1/sync/workspaces/{workspace.json()['id']}/members",
        json={
            "user_id": "reviewer",
            "role": "viewer",
            "permissions": ["resume.read"],
        },
    )
    assert member.status_code == 201
    assert member.json()["permissions_json"] == ["resume.read"]


def test_webhook_foundation_validates_events(client):
    created = client.post(
        "/api/v1/sync/webhooks",
        json={"url": "https://example.test/hook", "events": ["application.updated"]},
    )
    assert created.status_code == 201
    assert created.json()["events_json"] == ["application.updated"]

