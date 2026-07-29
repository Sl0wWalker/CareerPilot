from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal, require_role
from careerpilot.db.session import SessionLocal, get_db
from careerpilot.models.platform import ApiKey, PluginInstallation, WebhookSubscription
from careerpilot.schemas.platform import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
    DeveloperOverview,
    EventPublish,
    PluginRead,
    PluginUpdate,
    WebhookCreate,
    WebhookRead,
)
from careerpilot.services.platform import (
    PlatformEvent,
    authenticate_api_key,
    create_api_key,
    discover_plugins,
    event_bus,
    overview,
)

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])
Database = Annotated[Session, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(current_principal)]
AdminPrincipal = Annotated[Principal, Depends(require_role("owner", "admin"))]


@router.get("/overview", response_model=DeveloperOverview)
def developer_overview(db: Database, principal: CurrentPrincipal):
    return overview(db, principal.subject)


@router.get("/keys", response_model=list[ApiKeyRead])
def list_api_keys(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(ApiKey)
        .where(ApiKey.owner_id == principal.subject)
        .order_by(ApiKey.created_at.desc())
    ).all()


@router.post("/keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def issue_api_key(payload: ApiKeyCreate, db: Database, principal: CurrentPrincipal):
    record, secret = create_api_key(db, principal.subject, payload.name, payload.scopes)
    await event_bus.publish(
        PlatformEvent("platform.api_key.created", {"id": str(record.id), "name": record.name})
    )
    key_data = ApiKeyRead.model_validate(record).model_dump()
    return ApiKeyCreated(**key_data, secret=secret)


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: UUID, db: Database, principal: CurrentPrincipal):
    record = db.get(ApiKey, key_id)
    if record is None or record.owner_id != principal.subject:
        raise HTTPException(status_code=404, detail="API key not found")
    record.enabled = False
    db.commit()
    await event_bus.publish(PlatformEvent("platform.api_key.revoked", {"id": str(record.id)}))


@router.get("/webhooks", response_model=list[WebhookRead])
def list_webhooks(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(WebhookSubscription)
        .where(WebhookSubscription.owner_id == principal.subject)
        .order_by(WebhookSubscription.created_at.desc())
    ).all()


@router.post("/webhooks", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
def create_webhook(payload: WebhookCreate, db: Database, principal: CurrentPrincipal):
    import secrets

    record = WebhookSubscription(
        owner_id=principal.subject,
        url=str(payload.url),
        event_types=payload.event_types,
        description=payload.description,
        secret=secrets.token_urlsafe(32),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: UUID, db: Database, principal: CurrentPrincipal):
    record = db.get(WebhookSubscription, webhook_id)
    if record is None or record.owner_id != principal.subject:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(record)
    db.commit()


@router.get("/plugins", response_model=list[PluginRead])
def list_plugins(db: Database, principal: CurrentPrincipal):
    known = {
        plugin.plugin_id: plugin
        for plugin in db.scalars(
            select(PluginInstallation).where(PluginInstallation.owner_id == principal.subject)
        ).all()
    }
    changed = False
    for item in discover_plugins():
        if item["plugin_id"] not in known:
            plugin = PluginInstallation(owner_id=principal.subject, **item)
            db.add(plugin)
            known[plugin.plugin_id] = plugin
            changed = True
    if changed:
        db.commit()
    return sorted(known.values(), key=lambda item: item.name.lower())


@router.patch("/plugins/{plugin_id}", response_model=PluginRead)
def update_plugin(
    plugin_id: UUID, payload: PluginUpdate, db: Database, principal: CurrentPrincipal
):
    record = db.get(PluginInstallation, plugin_id)
    if record is None or record.owner_id != principal.subject:
        raise HTTPException(status_code=404, detail="Plugin not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def publish_event(payload: EventPublish, _: AdminPrincipal):
    await event_bus.publish(PlatformEvent(payload.event_type, payload.payload))
    return {"accepted": True}


@router.get("/public/status")
def public_api_status(
    db: Database,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
):
    if x_api_key is None or authenticate_api_key(db, x_api_key) is None:
        raise HTTPException(status_code=401, detail="A valid API key is required")
    return {"status": "ok", "api_version": "v1"}


@router.websocket("/events/ws")
async def websocket_events(websocket: WebSocket):
    key = websocket.query_params.get("api_key")
    with SessionLocal() as db:
        authenticated = bool(key and authenticate_api_key(db, key))
    if not authenticated:
        await websocket.close(code=4401, reason="A valid API key is required")
        return
    await websocket.accept()
    try:
        async for event in event_bus.stream():
            await websocket.send_json(
                {"type": event.event_type, "payload": event.payload}
            )
    except WebSocketDisconnect:
        return
