def test_maintenance_status_reports_governance(client):
    response = client.get("/api/v1/maintenance/status")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.0.0"
    assert all(body["governance_documents"].values())
    assert body["security_reporting"] == "GitHub private vulnerability reporting"

