import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models.sync import (
    ConnectedAccount,
    SyncChange,
    SyncConflict,
    SyncDevice,
    Workspace,
    WorkspaceMember,
)
from careerpilot.schemas.sync import ChangeInput, ConflictResolve, MemberCreate


def payload_checksum(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def register_device(db: Session, user_id: str, **values: str) -> SyncDevice:
    device = db.scalar(
        select(SyncDevice).where(
            SyncDevice.user_id == user_id, SyncDevice.device_key == values["device_key"]
        )
    )
    if device is None:
        device = SyncDevice(user_id=user_id, **values)
        db.add(device)
    else:
        device.display_name = values["display_name"]
        device.platform = values["platform"]
        device.revoked = False
    device.last_seen_at = datetime.now(UTC)
    db.commit()
    db.refresh(device)
    return device


def push_changes(
    db: Session, user_id: str, device_id: UUID, changes: list[ChangeInput]
) -> tuple[list[SyncChange], list[UUID]]:
    device = db.get(SyncDevice, device_id)
    if device is None or device.user_id != user_id or device.revoked:
        raise HTTPException(status_code=404, detail="Active sync device not found")
    accepted: list[SyncChange] = []
    conflicts: list[UUID] = []
    for incoming in changes:
        latest = db.scalar(
            select(SyncChange)
            .where(
                SyncChange.user_id == user_id,
                SyncChange.entity_type == incoming.entity_type,
                SyncChange.entity_key == incoming.entity_key,
            )
            .order_by(SyncChange.revision.desc())
        )
        next_revision = (latest.revision if latest else 0) + 1
        change = SyncChange(
            user_id=user_id,
            device_id=device.id,
            entity_type=incoming.entity_type,
            entity_key=incoming.entity_key,
            operation=incoming.operation,
            revision=next_revision,
            base_revision=incoming.base_revision,
            payload_json=incoming.payload,
            checksum=payload_checksum(incoming.payload),
        )
        db.add(change)
        db.flush()
        if latest and incoming.base_revision < latest.revision and latest.device_id != device.id:
            conflict = SyncConflict(
                user_id=user_id,
                entity_type=incoming.entity_type,
                entity_key=incoming.entity_key,
                local_change_id=change.id,
                remote_change_id=latest.id,
            )
            db.add(conflict)
            db.flush()
            conflicts.append(conflict.id)
        accepted.append(change)
    device.last_seen_at = datetime.now(UTC)
    db.commit()
    for change in accepted:
        db.refresh(change)
    return accepted, conflicts


def pull_changes(
    db: Session, user_id: str, cursor: int, limit: int
) -> tuple[int, list[SyncChange]]:
    changes = db.scalars(
        select(SyncChange)
        .where(SyncChange.user_id == user_id)
        .order_by(SyncChange.created_at, SyncChange.id)
        .offset(cursor)
        .limit(limit)
    ).all()
    return cursor + len(changes), list(changes)


def resolve_conflict(
    db: Session, user_id: str, conflict_id: UUID, payload: ConflictResolve
) -> SyncConflict:
    conflict = db.get(SyncConflict, conflict_id)
    if conflict is None or conflict.user_id != user_id:
        raise HTTPException(status_code=404, detail="Sync conflict not found")
    if payload.resolution == "merge" and payload.merged_payload is None:
        raise HTTPException(status_code=422, detail="Merged payload is required")
    source_id = (
        conflict.local_change_id
        if payload.resolution == "keep_local"
        else conflict.remote_change_id
    )
    source = db.get(SyncChange, source_id)
    conflict.resolution = payload.resolution
    conflict.resolved_payload_json = (
        payload.merged_payload if payload.resolution == "merge" else source.payload_json
    )
    conflict.status = "resolved"
    db.commit()
    db.refresh(conflict)
    return conflict


def ensure_workspace_access(
    db: Session, workspace_id: UUID, user_id: str, permission: str | None = None
) -> Workspace:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id == user_id:
        return workspace
    member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.status == "active",
        )
    )
    if member is None or (permission and permission not in member.permissions_json):
        raise HTTPException(status_code=403, detail="Workspace permission denied")
    return workspace


def add_member(
    db: Session, workspace: Workspace, owner_id: str, payload: MemberCreate
) -> WorkspaceMember:
    if workspace.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Only the workspace owner can add members")
    existing = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == payload.user_id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Workspace member already exists")
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=payload.user_id,
        role=payload.role,
        permissions_json=payload.permissions,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def integration_status(db: Session, user_id: str) -> dict[str, bool]:
    rows = db.execute(
        select(ConnectedAccount.provider, func.count(ConnectedAccount.id))
        .where(ConnectedAccount.user_id == user_id, ConnectedAccount.status == "connected")
        .group_by(ConnectedAccount.provider)
    ).all()
    return {provider: bool(count) for provider, count in rows}
