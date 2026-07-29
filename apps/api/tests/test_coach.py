from fastapi.testclient import TestClient


def create_profile(client: TestClient) -> None:
    response = client.post(
        "/profile",
        json={
            "first_name": "Test",
            "last_name": "Candidate",
            "skills": [{"name": "Python", "years_experience": 4}],
            "experiences": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "is_current": True,
                    "description": "Automated verification workflows and reduced runtime by 30%.",
                }
            ],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
            "job_preference": None,
        },
    )
    assert response.status_code == 201


def test_goals_dashboard_and_learning_plan(client: TestClient) -> None:
    create_profile(client)
    goal = client.post(
        "/coach/goals",
        json={"title": "Become a verification lead", "description": "Lead a team"},
    )
    assert goal.status_code == 200
    plan = client.post(
        "/coach/learning-plans",
        json={"target_role": "Python Kubernetes technical lead"},
    )
    assert plan.status_code == 200
    assert any(item["skill"] == "Kubernetes" for item in plan.json()["gap_analysis"])

    dashboard = client.get("/coach/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["active_goals"] == 1
    assert dashboard.json()["active_learning_plans"] == 1


def test_offer_comparison_is_explainable(client: TestClient) -> None:
    create_profile(client)
    response = client.post(
        "/coach/offers/compare",
        json={
            "title": "Two offers",
            "offers": [
                {"name": "A", "base_salary": 120000, "growth": 7},
                {"name": "B", "base_salary": 110000, "growth": 10},
            ],
            "weights": {"base_salary": 0.7, "growth": 0.3},
        },
    )
    assert response.status_code == 200
    assert len(response.json()["result"]["ranking"]) == 2
