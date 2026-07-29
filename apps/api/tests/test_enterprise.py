def create_org(client):
    response = client.post(
        "/api/v1/enterprise/organizations",
        json={"name": "CareerPilot Labs", "slug": "careerpilot-labs"},
    )
    assert response.status_code == 201
    return response.json()


def test_organization_workspace_membership_and_audit(client):
    organization = create_org(client)
    organization_id = organization["id"]

    workspace = client.post(
        f"/api/v1/enterprise/organizations/{organization_id}/workspaces",
        json={"name": "Hiring Operations", "slug": "hiring-ops"},
    )
    assert workspace.status_code == 201

    member = client.post(
        f"/api/v1/enterprise/organizations/{organization_id}/members",
        json={
            "subject": "operator@example.test",
            "role": "manager",
            "permissions": ["usage:read"],
        },
    )
    assert member.status_code == 201
    members = client.get(f"/api/v1/enterprise/organizations/{organization_id}/members").json()
    assert {item["role"] for item in members} == {"owner", "manager"}

    audit = client.get(f"/api/v1/enterprise/organizations/{organization_id}/audit")
    assert audit.status_code == 200
    assert {item["action"] for item in audit.json()} >= {
        "organization.created",
        "workspace.created",
        "membership.created",
    }


def test_policy_sso_quota_and_agent_orchestration(client):
    organization_id = create_org(client)["id"]
    sso = client.put(
        f"/api/v1/enterprise/organizations/{organization_id}/sso",
        json={
            "protocol": "oidc",
            "issuer": "https://identity.example.test",
            "client_id": "careerpilot",
            "enabled": True,
        },
    )
    assert sso.status_code == 200
    assert sso.json()["protocol"] == "oidc"

    policy = client.put(
        f"/api/v1/enterprise/organizations/{organization_id}/policies",
        json={
            "key": "agents.require_human_review",
            "value": {"enabled": True},
            "enforcement": "enforce",
        },
    )
    assert policy.status_code == 200

    quota = client.put(
        f"/api/v1/enterprise/organizations/{organization_id}/quotas",
        json={"metric": "agent_runs", "limit": 1},
    )
    assert quota.status_code == 200

    run = client.post(
        f"/api/v1/enterprise/organizations/{organization_id}/agents",
        json={
            "agent_type": "application-orchestrator",
            "objective": "Prepare one supervised application",
            "input": {"job_id": "test-job"},
        },
    )
    assert run.status_code == 202
    assert run.json()["status"] == "queued"
    assert (
        client.post(
            f"/api/v1/enterprise/organizations/{organization_id}/agents",
            json={
                "agent_type": "application-orchestrator",
                "objective": "Prepare another application",
            },
        ).status_code
        == 429
    )

    memory = client.put(
        f"/api/v1/enterprise/organizations/{organization_id}/agent-memory",
        json={
            "namespace": "application-policy",
            "key": "review",
            "value": {"required": True},
        },
    )
    assert memory.status_code == 200
    overview = client.get("/api/v1/enterprise/overview").json()
    assert overview["organizations"] == 1
    assert overview["active_agents"] == 1
    assert overview["quota_utilization"]["agent_runs"] == 1.0
