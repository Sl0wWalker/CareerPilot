import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.core.config import Settings, get_settings
from careerpilot.core.security import (
    Principal,
    create_access_token,
    current_principal,
    hash_password,
    require_role,
    verify_password,
)
from careerpilot.db.session import get_db
from careerpilot.models.release import AuditEvent, User

router = APIRouter(prefix="/api/v1", tags=["release"])
OwnerPrincipal = Annotated[Principal, Depends(require_role("owner", "admin"))]
Database = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Database, settings: AppSettings):
    if db.scalar(select(User.id).limit(1)) is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is closed after the owner account is created",
        )
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id), user.role, settings))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database, settings: AppSettings):
    user = db.scalar(select(User).where(User.email == payload.email))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id), user.role, settings))


@router.get("/auth/me")
def me(principal: Annotated[Principal, Depends(current_principal)]) -> dict[str, str]:
    return {"id": principal.subject, "role": principal.role}


@router.get("/audit")
def audit_events(
    db: Database,
    _: OwnerPrincipal,
) -> list[dict[str, object]]:
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [
        {
            "id": str(event.id),
            "action": event.action,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "created_at": event.created_at,
        }
        for event in events
    ]


@router.post("/backups", status_code=201)
def create_backup(
    request: Request,
    db: Database,
    settings: AppSettings,
    principal: OwnerPrincipal,
) -> dict[str, str]:
    if not settings.database_url.startswith("sqlite:///"):
        raise HTTPException(status_code=400, detail="Built-in backup currently supports SQLite")
    source = Path(settings.database_url.removeprefix("sqlite:///")).resolve()
    if not source.exists():
        raise HTTPException(status_code=404, detail="Database file does not exist")
    directory = Path(settings.backup_directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"careerpilot-{datetime.now(UTC):%Y%m%d-%H%M%S}.db"
    shutil.copy2(source, destination)
    db.add(
        AuditEvent(
            actor_id=principal.subject,
            action="backup.created",
            resource_type="database",
            resource_id=destination.name,
            request_id=getattr(request.state, "request_id", None),
            details_json=json.dumps({"path": str(destination)}),
        )
    )
    db.commit()
    return {"filename": destination.name, "path": str(destination)}
