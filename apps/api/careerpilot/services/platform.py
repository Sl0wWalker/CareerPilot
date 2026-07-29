import asyncio
import hashlib
import importlib.metadata
import secrets
from collections import defaultdict
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models.platform import ApiKey, PluginInstallation, WebhookSubscription
from careerpilot.schemas.platform import DeveloperOverview


@dataclass(frozen=True)
class PlatformEvent:
    event_type: str
    payload: dict[str, Any]


EventHandler = Callable[[PlatformEvent], Awaitable[None]]


class EventBus:
    """Small async event bus used by modules and the live-event API."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._subscribers: set[asyncio.Queue[PlatformEvent]] = set()

    def subscribe(self, event_type: str, handler: EventHandler) -> Callable[[], None]:
        self._handlers[event_type].append(handler)

        def unsubscribe() -> None:
            self._handlers[event_type].remove(handler)

        return unsubscribe

    async def publish(self, event: PlatformEvent) -> None:
        handlers = [*self._handlers.get(event.event_type, []), *self._handlers.get("*", [])]
        if handlers:
            await asyncio.gather(*(handler(event) for handler in handlers))
        for queue in tuple(self._subscribers):
            queue.put_nowait(event)

    async def stream(self) -> AsyncIterator[PlatformEvent]:
        queue: asyncio.Queue[PlatformEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)


event_bus = EventBus()


class AIProviderPlugin(Protocol):
    plugin_id: str

    async def generate(self, prompt: str) -> str: ...


class JobSourcePlugin(Protocol):
    plugin_id: str

    async def search(self, query: dict[str, Any]) -> list[dict[str, Any]]: ...


class AutomationAdapterPlugin(Protocol):
    plugin_id: str

    async def can_handle(self, url: str) -> bool: ...


PLUGIN_GROUPS = {
    "ai_provider": "careerpilot.ai_providers",
    "job_source": "careerpilot.job_sources",
    "automation_adapter": "careerpilot.automation_adapters",
}


def discover_plugins() -> list[dict[str, str]]:
    discovered: list[dict[str, str]] = []
    entry_points = importlib.metadata.entry_points()
    for plugin_type, group in PLUGIN_GROUPS.items():
        for entry in entry_points.select(group=group):
            distribution = entry.dist
            discovered.append(
                {
                    "plugin_id": entry.name,
                    "name": entry.name.replace("-", " ").title(),
                    "version": distribution.version if distribution else "unknown",
                    "plugin_type": plugin_type,
                }
            )
    return discovered


def create_api_key(db: Session, owner_id: str, name: str, scopes: list[str]) -> tuple[ApiKey, str]:
    secret = f"cp_{secrets.token_urlsafe(32)}"
    prefix = secret[:12]
    record = ApiKey(
        owner_id=owner_id,
        name=name,
        prefix=prefix,
        secret_hash=hashlib.sha256(secret.encode()).hexdigest(),
        scopes=sorted(set(scopes)),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, secret


def authenticate_api_key(db: Session, secret: str) -> ApiKey | None:
    prefix = secret[:12]
    record = db.scalar(
        select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.enabled.is_(True))
    )
    if record is None:
        return None
    actual = hashlib.sha256(secret.encode()).hexdigest()
    return record if secrets.compare_digest(actual, record.secret_hash) else None


def overview(db: Session, owner_id: str) -> DeveloperOverview:
    return DeveloperOverview(
        api_version="v1",
        openapi_url="/openapi.json",
        websocket_url="/api/v1/platform/events/ws",
        api_keys=db.scalar(
            select(func.count(ApiKey.id)).where(ApiKey.owner_id == owner_id)
        )
        or 0,
        webhooks=db.scalar(
            select(func.count(WebhookSubscription.id)).where(
                WebhookSubscription.owner_id == owner_id
            )
        )
        or 0,
        plugins=db.scalar(
            select(func.count(PluginInstallation.id)).where(
                PluginInstallation.owner_id == owner_id
            )
        )
        or 0,
        extension_types=list(PLUGIN_GROUPS),
    )

