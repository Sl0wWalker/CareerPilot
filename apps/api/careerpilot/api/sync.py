from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal
from careerpilot.db.session import get_db
from careerpilot.models.sync import (
    ConnectedAccount,
    SyncConflict,
    SyncDevice,
    WebhookEndpoint,
    Workspace,
    WorkspaceMember,
)
from careerpilot.schemas.sync import (
    AccountCreate,
    AccountRead,
    ConflictRead,
    ConflictResolve,
    DeviceRead,
    DeviceRegister,
    IntegrationDescriptor,
    MemberCreate,
    MemberRead,
    PushRequest,
    SyncBatch,
    WebhookCreate,
    WebhookRead,
    WorkspaceCreate,
    WorkspaceRead,
)
from careerpilot.services.sync import (
    add_member,
    ensure_workspace_access,
    integration_status,
    pull_changes,
    push_changes,
    register_device,
    resolve_conflict,
)

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])
Database = Annotated[Session, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(current_principal)]

PROVIDERS = {
    "gmail": ("communication", ["job-alert import", "application receipt import"]),
    "google_calendar": ("calendar", ["application reminders", "interview export"]),
    "google_drive": ("storage", ["resume export", "backup"]),
    "onedrive": ("storage", ["resume export", "backup"]),
    "dropbox": ("storage", ["resume export", "backup"]),
    "linkedin": ("career", ["profile import", "profile export"]),
}


@router.post("/devices", response_model=DeviceRead, status_code=201)
def create_device(payload: DeviceRegister, db: Database, principal: CurrentPrincipal):
    return register_device(db, principal.subject, **payload.model_dump())


@router.get("/devices", response_model=list[DeviceRead])
def devices(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(SyncDevice)
        .where(SyncDevice.user_id == principal.subject)
        .order_by(SyncDevice.created_at.desc())
    ).all()


@router.delete("/devices/{device_id}", status_code=204)
def revoke_device(device_id: UUID, db: Database, principal: CurrentPrincipal):
    device = db.get(SyncDevice, device_id)
    if device is None or device.user_id != principal.subject:
        raise HTTPException(status_code=404, detail="Sync device not found")
    device.revoked = True
    db.commit()


@router.post("/push", response_model=SyncBatch)
def push(payload: PushRequest, db: Database, principal: CurrentPrincipal):
    accepted, conflicts = push_changes(db, principal.subject, payload.device_id, payload.changes)
    cursor, _ = pull_changes(db, principal.subject, 0, 1_000_000)
    return SyncBatch(cursor=cursor, accepted=accepted, conflicts=conflicts)


@router.get("/pull", response_model=SyncBatch)
def pull(
    db: Database,
    principal: CurrentPrincipal,
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
):
    next_cursor, changes = pull_changes(db, principal.subject, cursor, limit)
    return SyncBatch(cursor=next_cursor, accepted=changes, conflicts=[])


@router.get("/conflicts", response_model=list[ConflictRead])
def conflicts(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(SyncConflict).where(
            SyncConflict.user_id == principal.subject, SyncConflict.status == "open"
        )
    ).all()


@router.post("/conflicts/{conflict_id}/resolve", response_model=ConflictRead)
def resolve(
    conflict_id: UUID, payload: ConflictResolve, db: Database, principal: CurrentPrincipal
):
    return resolve_conflict(db, principal.subject, conflict_id, payload)


@router.get("/integrations", response_model=list[IntegrationDescriptor])
def integrations(db: Database, principal: CurrentPrincipal):
    connected = integration_status(db, principal.subject)
    return [
        IntegrationDescriptor(
            provider=provider,
            category=details[0],
            capabilities=details[1],
            permitted_use="User-authorized import/export only; no credential values are stored.",
            connected=connected.get(provider, False),
        )
        for provider, details in PROVIDERS.items()
    ]


@router.post("/accounts", response_model=AccountRead, status_code=201)
def connect_account(payload: AccountCreate, db: Database, principal: CurrentPrincipal):
    if payload.provider not in PROVIDERS:
        raise HTTPException(status_code=422, detail="Unsupported integration provider")
    account = ConnectedAccount(
        user_id=principal.subject,
        provider=payload.provider,
        external_account_id=payload.external_account_id,
        display_name=payload.display_name,
        scopes_json=payload.scopes,
        credential_reference=payload.credential_reference,
        status="connected" if payload.credential_reference else "pending",
    )
    db.add(account)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Account is already connected") from exc
    db.refresh(account)
    return account


@router.get("/accounts", response_model=list[AccountRead])
def accounts(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(ConnectedAccount).where(ConnectedAccount.user_id == principal.subject)
    ).all()


@router.delete("/accounts/{account_id}", status_code=204)
def disconnect_account(account_id: UUID, db: Database, principal: CurrentPrincipal):
    account = db.get(ConnectedAccount, account_id)
    if account is None or account.user_id != principal.subject:
        raise HTTPException(status_code=404, detail="Connected account not found")
    db.delete(account)
    db.commit()


@router.post("/workspaces", response_model=WorkspaceRead, status_code=201)
def create_workspace(payload: WorkspaceCreate, db: Database, principal: CurrentPrincipal):
    workspace = Workspace(owner_id=principal.subject, **payload.model_dump())
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/workspaces", response_model=list[WorkspaceRead])
def workspaces(db: Database, principal: CurrentPrincipal):
    member_ids = select(WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == principal.subject, WorkspaceMember.status == "active"
    )
    return db.scalars(
        select(Workspace).where(
            (Workspace.owner_id == principal.subject) | (Workspace.id.in_(member_ids))
        )
    ).all()


@router.post("/workspaces/{workspace_id}/members", response_model=MemberRead, status_code=201)
def create_member(
    workspace_id: UUID, payload: MemberCreate, db: Database, principal: CurrentPrincipal
):
    workspace = ensure_workspace_access(db, workspace_id, principal.subject)
    return add_member(db, workspace, principal.subject, payload)


@router.get("/workspaces/{workspace_id}/members", response_model=list[MemberRead])
def members(workspace_id: UUID, db: Database, principal: CurrentPrincipal):
    ensure_workspace_access(db, workspace_id, principal.subject)
    return db.scalars(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    ).all()


@router.post("/webhooks", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
def create_webhook(payload: WebhookCreate, db: Database, principal: CurrentPrincipal):
    hook = WebhookEndpoint(
        user_id=principal.subject,
        url=str(payload.url),
        events_json=payload.events,
        secret_reference=payload.secret_reference,
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return hook


@router.get("/webhooks", response_model=list[WebhookRead])
def webhooks(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(WebhookEndpoint).where(WebhookEndpoint.user_id == principal.subject)
    ).all()

