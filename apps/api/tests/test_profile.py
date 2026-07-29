from fastapi.testclient import TestClient

PROFILE = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "linkedin_url": "https://www.linkedin.com/in/ada",
    "experiences": [
        {
            "company": "Analytical Engines",
            "title": "Programmer",
            "start_date": "2020-01-01",
            "end_date": "2022-12-31",
            "description": "Developed an algorithm for the analytical engine.",
        }
    ],
    "education": [
        {
            "institution": "Private Study",
            "degree": "Mathematics",
            "start_year": 2000,
            "end_year": 2005,
        }
    ],
    "projects": [
        {
            "name": "Bernoulli Algorithm",
            "description": "A method for calculating Bernoulli numbers.",
            "url": "https://example.com/bernoulli",
        }
    ],
    "skills": [{"name": "Mathematics", "years_experience": 15, "proficiency": "expert"}],
    "certifications": [{"name": "Fictional test credential", "issuer": "Test issuer"}],
    "achievements": [{"title": "First program", "description": "Published a complete algorithm."}],
    "job_preference": {
        "target_roles": "Computing researcher",
        "preferred_locations": "Remote",
        "remote_ok": True,
        "minimum_salary": 100000,
        "requires_sponsorship": False,
    },
}


def test_profile_lifecycle_and_relationship_persistence(client: TestClient) -> None:
    missing = client.get("/profile")
    assert missing.status_code == 404

    created = client.post("/profile", json=PROFILE)
    assert created.status_code == 201
    body = created.json()
    assert body["first_name"] == "Ada"
    assert body["experiences"][0]["company"] == "Analytical Engines"
    assert body["education"][0]["degree"] == "Mathematics"
    assert body["projects"][0]["name"] == "Bernoulli Algorithm"
    assert body["skills"][0]["name"] == "Mathematics"
    assert body["certifications"][0]["issuer"] == "Test issuer"
    assert body["achievements"][0]["title"] == "First program"
    assert body["job_preference"]["remote_ok"] is True

    retrieved = client.get("/profile/full")
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == body["id"]
    assert len(retrieved.json()["experiences"]) == 1

    updated = client.patch("/profile", json={"city": "London", "first_name": "Augusta Ada"})
    assert updated.status_code == 200
    assert updated.json()["city"] == "London"
    assert updated.json()["first_name"] == "Augusta Ada"
    assert updated.json()["skills"][0]["id"] == body["skills"][0]["id"]
    assert updated.json()["skills"][0]["name"] == "Mathematics"


def test_rejects_second_profile_and_invalid_relationship_dates(client: TestClient) -> None:
    assert client.post("/profile", json=PROFILE).status_code == 201
    assert client.post("/profile", json=PROFILE).status_code == 409

    invalid = dict(PROFILE)
    invalid["email"] = "not-an-email"
    assert client.post("/profile", json=invalid).status_code == 422
