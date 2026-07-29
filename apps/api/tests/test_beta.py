def test_beta_settings_are_private_and_opt_in(client):
    initial = client.get("/api/v1/beta/settings")
    assert initial.status_code == 200
    assert initial.json()["analytics_opt_in"] is False

    updated = client.patch(
        "/api/v1/beta/settings",
        json={
            "enrolled": True,
            "analytics_opt_in": True,
            "diagnostics_opt_in": True,
            "release_channel": "beta",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["release_channel"] == "beta"


def test_feedback_diagnostics_require_opt_in(client):
    created = client.post(
        "/api/v1/beta/feedback",
        json={
            "kind": "bug",
            "title": "Form field is not filled",
            "description": "A test description",
            "diagnostics": {"browser": "test"},
        },
    )
    assert created.status_code == 201
    assert created.json()["diagnostics_json"] == {}

    client.patch("/api/v1/beta/settings", json={"diagnostics_opt_in": True})
    opted_in = client.post(
        "/api/v1/beta/feedback",
        json={
            "kind": "feature",
            "title": "Add another ATS",
            "description": "Please support a test ATS",
            "diagnostics": {"version": "1.0"},
        },
    )
    assert opted_in.status_code == 201
    assert opted_in.json()["diagnostics_json"] == {"version": "1.0"}


def test_usage_events_rejected_until_opt_in(client):
    payload = {
        "anonymous_id": "anonymous-test-id",
        "event_name": "workspace.opened",
        "properties": {},
    }
    assert client.post("/api/v1/beta/events", json=payload).status_code == 403
    client.patch("/api/v1/beta/settings", json={"analytics_opt_in": True})
    assert client.post("/api/v1/beta/events", json=payload).status_code == 202


def test_admin_health_and_feature_flag_evaluation(client):
    flag = client.post(
        "/api/v1/beta/admin/flags",
        json={
            "key": "beta.new_dashboard",
            "description": "New beta dashboard",
            "enabled": True,
            "beta_only": True,
            "rollout_percentage": 100,
            "config": {"layout": "compact"},
        },
    )
    assert flag.status_code == 201
    assert client.get("/api/v1/beta/flags").json()[0]["enabled"] is False
    client.patch("/api/v1/beta/settings", json={"enrolled": True})
    evaluated = client.get("/api/v1/beta/flags").json()[0]
    assert evaluated == {
        "key": "beta.new_dashboard",
        "enabled": True,
        "config": {"layout": "compact"},
    }
    assert client.get("/api/v1/beta/admin/health").status_code == 200

