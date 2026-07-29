from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal
from careerpilot.db.session import get_db
from careerpilot.models.global_platform import (
    GlobalPreference,
    MobileEndpoint,
    ModelRoutingPolicy,
    NotificationDelivery,
)
from careerpilot.schemas.global_platform import (
    GlobalPreferenceRead,
    GlobalPreferenceUpsert,
    MobileEndpointCreate,
    NotificationCreate,
    RoutingPolicyUpsert,
)
from careerpilot.services.global_platform import routing_decision

router = APIRouter(prefix="/api/v1/global", tags=["global-platform"])
Database = Annotated[Session, Depends(get_db)]
User = Annotated[Principal, Depends(current_principal)]


@router.get("/preferences", response_model=GlobalPreferenceRead | None)
def get_preferences(db: Database, principal: User):
    return db.scalar(select(GlobalPreference).where(GlobalPreference.owner_id == principal.subject))


@router.put("/preferences", response_model=GlobalPreferenceRead)
def upsert_preferences(payload: GlobalPreferenceUpsert, db: Database, principal: User):
    item = db.scalar(select(GlobalPreference).where(GlobalPreference.owner_id == principal.subject))
    if item is None:
        item = GlobalPreference(owner_id=principal.subject, **payload.model_dump())
        db.add(item)
    else:
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.put("/routing/{task_type}")
def upsert_routing(task_type: str, payload: RoutingPolicyUpsert, db: Database, principal: User):
    if task_type != payload.task_type:
        raise HTTPException(status_code=422, detail="Task type does not match path")
    item = db.scalar(
        select(ModelRoutingPolicy).where(
            ModelRoutingPolicy.owner_id == principal.subject,
            ModelRoutingPolicy.task_type == task_type,
        )
    )
    if item is None:
        item = ModelRoutingPolicy(owner_id=principal.subject, **payload.model_dump())
        db.add(item)
    else:
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return {"task_type": item.task_type, "policy": payload.model_dump()}


@router.get("/routing/{task_type}/decision")
def decide_route(
    task_type: str,
    db: Database,
    principal: User,
    local_available: bool = Query(default=True),
):
    item = db.scalar(
        select(ModelRoutingPolicy).where(
            ModelRoutingPolicy.owner_id == principal.subject,
            ModelRoutingPolicy.task_type == task_type,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Routing policy not found")
    return routing_decision(item, local_available)


@router.post("/mobile/endpoints", status_code=201)
def register_endpoint(payload: MobileEndpointCreate, db: Database, principal: User):
    item = db.scalar(
        select(MobileEndpoint).where(
            MobileEndpoint.owner_id == principal.subject,
            MobileEndpoint.device_id == payload.device_id,
        )
    )
    if item is None:
        item = MobileEndpoint(owner_id=principal.subject, **payload.model_dump())
        db.add(item)
    else:
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "device_id": item.device_id, "platform": item.platform}


@router.post("/notifications", status_code=202)
def queue_notification(payload: NotificationCreate, db: Database, principal: User):
    delivery = NotificationDelivery(
        owner_id=principal.subject,
        endpoint_id=str(payload.endpoint_id) if payload.endpoint_id else None,
        category=payload.category,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return {"id": delivery.id, "status": delivery.status}
