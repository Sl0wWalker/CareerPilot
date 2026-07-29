def package_payload(slug="ats-resume-pack", version="1.0.0"):
    return {
        "slug": slug,
        "name": "ATS Resume Pack",
        "summary": "Original ATS-safe resume layouts and prompts.",
        "package_type": "resume_template",
        "version": version,
        "channel": "stable",
        "manifest": {"entrypoint": "templates/index.json"},
        "dependencies": [],
        "permissions": ["documents.read", "documents.write"],
    }


def test_publish_install_review_and_uninstall(client):
    published = client.post("/api/v1/marketplace/packages", json=package_payload())
    assert published.status_code == 201, published.text
    package = published.json()
    assert len(package["signature"]) == 64
    assert client.get("/api/v1/marketplace/packages").json()[0]["slug"] == package["slug"]

    installed = client.post(
        f"/api/v1/marketplace/packages/{package['id']}/install",
        json={"channel": "stable", "configuration": {"theme": "compact"}},
    )
    assert installed.status_code == 200, installed.text
    assert installed.json()["enabled"] is True

    reviewed = client.post(
        f"/api/v1/marketplace/packages/{package['id']}/reviews",
        json={"rating": 5, "body": "Useful and transparent."},
    )
    assert reviewed.status_code == 201
    assert client.get("/api/v1/marketplace/packages").json()[0]["rating"] == 5

    installation_id = installed.json()["id"]
    assert client.delete(f"/api/v1/marketplace/installations/{installation_id}").status_code == 204


def test_package_permissions_and_dependencies_are_enforced(client):
    unsafe = package_payload("unsafe-pack")
    unsafe["permissions"] = ["filesystem.unrestricted"]
    assert client.post("/api/v1/marketplace/packages", json=unsafe).status_code == 422

    dependent = package_payload("dependent-pack")
    dependent["dependencies"] = [{"slug": "missing-pack", "version": ">=1.0.0"}]
    created = client.post("/api/v1/marketplace/packages", json=dependent).json()
    response = client.post(
        f"/api/v1/marketplace/packages/{created['id']}/install",
        json={"channel": "stable"},
    )
    assert response.status_code == 409


def test_workflow_approval_gate(client):
    workflow = client.post(
        "/api/v1/marketplace/workflows",
        json={
            "name": "Tailor and review",
            "description": "Draft a resume and require approval.",
            "trigger_type": "manual",
            "graph": {
                "nodes": [
                    {"id": "draft", "type": "ai", "config": {"prompt": "Tailor resume"}},
                    {"id": "approve", "type": "approval", "config": {"message": "Review draft"}},
                ],
                "edges": [{"source": "draft", "target": "approve"}],
            },
        },
    )
    assert workflow.status_code == 201, workflow.text
    execution = client.post(
        f"/api/v1/marketplace/workflows/{workflow.json()['id']}/execute?dry_run=true",
        json={"job_id": "test"},
    )
    assert execution.status_code == 200, execution.text
    assert execution.json()["status"] == "awaiting_approval"
    approved = client.post(f"/api/v1/marketplace/executions/{execution.json()['id']}/approve")
    assert approved.json()["status"] == "completed"
