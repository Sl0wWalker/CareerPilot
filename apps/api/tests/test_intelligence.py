def test_strategy_monitor_and_overview(client):
    strategy = client.post(
        "/api/v1/intelligence/strategies",
        json={
            "title": "Formal verification leadership",
            "horizon_months": 18,
            "target_roles": ["Staff Verification Engineer"],
            "objectives": [{"milestone": "Lead a verification initiative"}],
            "constraints": {"sponsorship_required": True},
        },
    )
    assert strategy.status_code == 201

    monitor = client.post(
        "/api/v1/intelligence/monitors",
        json={
            "name": "High-fit verification roles",
            "criteria": {"minimum_match": 85},
            "cadence": "daily",
        },
    )
    assert monitor.status_code == 201
    queued = client.post(f"/api/v1/intelligence/monitors/{monitor.json()['id']}/run")
    assert queued.status_code == 200
    assert queued.json()["approval_required_for_external_actions"] is True

    overview = client.get("/api/v1/intelligence/overview")
    assert overview.status_code == 200
    assert overview.json()["strategies"] == 1
    assert overview.json()["active_monitors"] == 1


def test_agent_governance_and_skill_forecast(client):
    agent = client.put(
        "/api/v1/intelligence/agents/opportunity-scout",
        json={
            "agent_key": "opportunity-scout",
            "display_name": "Opportunity Scout",
            "objective": "Find and rank suitable opportunities",
            "enabled": True,
            "autonomy_level": "prepare",
            "approval_policy": {"applications.submit": "always"},
            "capabilities": ["jobs.search", "matching.analyze", "documents.prepare"],
            "schedule": {"cadence": "daily"},
        },
    )
    assert agent.status_code == 200
    assert agent.json()["autonomy_level"] == "prepare"

    unsafe = client.put(
        "/api/v1/intelligence/agents/unsafe-agent",
        json={
            "agent_key": "unsafe-agent",
            "display_name": "Unsafe Agent",
            "objective": "Submit without review",
            "enabled": True,
            "autonomy_level": "execute",
            "approval_policy": {"applications.submit": "never"},
            "capabilities": ["applications.submit"],
        },
    )
    assert unsafe.status_code == 422

    forecast = client.put(
        "/api/v1/intelligence/forecasts/Python",
        json={
            "skill": "Python",
            "current_demand": 0.6,
            "projected_demand": 0.8,
            "confidence": 0.9,
            "evidence": [{"source": "normalized_jobs", "count": 100}],
        },
    )
    assert forecast.status_code == 200
    assert forecast.json()["trend"] == "rising"

    governance = client.get("/api/v1/intelligence/governance")
    assert governance.status_code == 200
    assert "applications.submit" in governance.json()["external_actions_always_gated"]

