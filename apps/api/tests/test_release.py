from careerpilot.core.config import Settings
from careerpilot.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_token_roundtrip():
    encoded = hash_password("a-long-test-password")
    assert verify_password("a-long-test-password", encoded)
    assert not verify_password("wrong-password", encoded)
    settings = Settings(secret_key="x" * 32)
    token = create_access_token("user-1", "owner", settings)
    assert decode_access_token(token, settings).subject == "user-1"


def test_register_login_and_diagnostics(client):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "password": "a-long-test-password"},
    )
    assert register.status_code == 201
    assert register.json()["access_token"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "a-long-test-password"},
    )
    assert login.status_code == 200
    diagnostics = client.get("/diagnostics")
    assert diagnostics.status_code == 200
    assert diagnostics.json()["version"] == "1.0.0"
    assert diagnostics.headers["x-content-type-options"] == "nosniff"
