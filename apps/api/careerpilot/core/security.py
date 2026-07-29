import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from careerpilot.core.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    salt_text = base64.urlsafe_b64encode(salt).decode()
    digest_text = base64.urlsafe_b64encode(digest).decode()
    return f"pbkdf2_sha256$310000${salt_text}${digest_text}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, rounds, salt, expected = encoded.split("$", 3)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.urlsafe_b64decode(salt), int(rounds)
        )
        return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode(), expected)
    except (ValueError, TypeError):
        return False


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(subject: str, role: str, settings: Settings) -> str:
    payload = {
        "sub": subject,
        "role": role,
        "exp": int(time.time()) + settings.access_token_minutes * 60,
    }
    body = _encode(json.dumps(payload, separators=(",", ":")).encode())
    digest = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    signature = _encode(digest)
    return f"{body}.{signature}"


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str


def decode_access_token(token: str, settings: Settings) -> Principal:
    try:
        body, signature = token.split(".", 1)
        expected = _encode(
            hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = json.loads(_decode(body))
        if payload["exp"] < time.time():
            raise ValueError
        return Principal(subject=payload["sub"], role=payload["role"])
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    if not settings.auth_enabled:
        return Principal(subject="local-user", role="owner")
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return decode_access_token(credentials.credentials, settings)


def require_role(*roles: str):
    def dependency(
        principal: Annotated[Principal, Depends(current_principal)],
    ) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency
