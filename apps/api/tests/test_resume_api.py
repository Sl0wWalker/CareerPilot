from fastapi.testclient import TestClient

PROFILE = {
    "first_name": "Test",
    "last_name": "Candidate",
    "email": "candidate@example.com",
}

RESUME = b"""
SUMMARY
Automation engineer
SKILLS
Python, SQL, Python
EXPERIENCE
Engineer | Example Corp | 2020 - 2022
EDUCATION
BS Computer Engineering | State University | 2016 - 2020
PROJECTS
Deterministic resume parser
CERTIFICATIONS
Test certification
AWARDS
Automation award
"""


def create_profile(client: TestClient) -> None:
    assert client.post("/profile", json=PROFILE).status_code == 201


def test_import_review_edit_approve_and_delete(client: TestClient) -> None:
    create_profile(client)
    imported = client.post(
        "/resume/import",
        params={"filename": "resume.txt"},
        content=RESUME,
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 201
    body = imported.json()
    assert body["parsing_status"] == "review_required"
    assert body["parser_version"] == "deterministic-1"
    assert any(fact["entity_type"] == "experience" for fact in body["facts"])
    assert any("Duplicate skill" in warning for warning in body["warnings"])

    import_id = body["id"]
    assert client.get("/resume/imports").json()[0]["id"] == import_id
    assert client.get(f"/resume/import/{import_id}").status_code == 200
    review = client.get(f"/resume/import/{import_id}/review")
    assert review.status_code == 200

    skill = next(fact for fact in body["facts"] if fact["entity_type"] == "skill")
    edited = client.patch(
        f"/resume/import/{import_id}/fact/{skill['id']}",
        json={"payload": {"name": "Python 3"}, "approved": True},
    )
    assert edited.status_code == 200
    updated_skill = next(fact for fact in edited.json()["facts"] if fact["id"] == skill["id"])
    assert updated_skill["payload"]["name"] == "Python 3"
    assert updated_skill["approved"] is True

    approved = client.post(
        f"/resume/import/{import_id}/approve",
        json={"fact_ids": [fact["id"] for fact in edited.json()["facts"]]},
    )
    assert approved.status_code == 200
    assert approved.json()["parsing_status"] == "approved"
    profile = client.get("/profile/full").json()
    assert any(item["name"] == "Python 3" for item in profile["skills"])
    assert any(item["company"] == "Example Corp" for item in profile["experiences"])

    deleted = client.delete(f"/resume/import/{import_id}")
    assert deleted.status_code == 204
    assert client.get(f"/resume/import/{import_id}").status_code == 404


def test_duplicate_and_malformed_imports(client: TestClient) -> None:
    create_profile(client)
    first = client.post(
        "/resume/import",
        params={"filename": "resume.txt"},
        content=RESUME,
        headers={"Content-Type": "text/plain"},
    )
    duplicate = client.post(
        "/resume/import",
        params={"filename": "resume.txt"},
        content=RESUME,
        headers={"Content-Type": "text/plain"},
    )
    malformed = client.post(
        "/resume/import",
        params={"filename": "resume.pdf"},
        content=b"not a pdf",
        headers={"Content-Type": "application/pdf"},
    )
    unsupported = client.post(
        "/resume/import",
        params={"filename": "resume.rtf"},
        content=b"resume",
        headers={"Content-Type": "application/rtf"},
    )
    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert malformed.status_code == 422
    assert unsupported.status_code == 422
