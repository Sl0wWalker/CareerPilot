from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal, require_role
from careerpilot.db.session import get_db
from careerpilot.models.beta import FeatureFlag, FeedbackItem, SatisfactionResponse, UsageEvent
from careerpilot.schemas.beta import (
    BetaPreferenceRead,
    BetaPreferenceUpdate,
    FeatureFlagCreate,
    FeatureFlagRead,
    FeedbackCreate,
    FeedbackRead,
    FeedbackUpdate,
    FlagEvaluation,
    ProductHealth,
    SatisfactionCreate,
    UsageEventCreate,
)
from careerpilot.services.beta import find_feedback, flag_enabled, get_preferences, product_health

router = APIRouter(prefix="/api/v1/beta", tags=["beta"])
Database = Annotated[Session, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(current_principal)]
AdminPrincipal = Annotated[Principal, Depends(require_role("owner", "admin"))]


@router.get("/settings", response_model=BetaPreferenceRead)
def read_settings(db: Database, principal: CurrentPrincipal):
    return get_preferences(db, principal.subject)


@router.patch("/settings", response_model=BetaPreferenceRead)
def update_settings(payload: BetaPreferenceUpdate, db: Database, principal: CurrentPrincipal):
    preferences = get_preferences(db, principal.subject)
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(preferences, key, value)
    db.commit()
    db.refresh(preferences)
    return preferences


@router.post("/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate, db: Database, principal: CurrentPrincipal):
    preferences = get_preferences(db, principal.subject)
    diagnostics = payload.diagnostics if preferences.diagnostics_opt_in else {}
    item = FeedbackItem(
        user_id=principal.subject,
        kind=payload.kind,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        page_url=payload.page_url,
        diagnostics_json=diagnostics,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/feedback", response_model=list[FeedbackRead])
def list_own_feedback(db: Database, principal: CurrentPrincipal):
    return db.scalars(
        select(FeedbackItem)
        .where(FeedbackItem.user_id == principal.subject)
        .order_by(FeedbackItem.created_at.desc())
    ).all()


@router.post("/satisfaction", status_code=status.HTTP_201_CREATED)
def satisfaction(payload: SatisfactionCreate, db: Database, principal: CurrentPrincipal):
    response = SatisfactionResponse(user_id=principal.subject, **payload.model_dump())
    db.add(response)
    db.commit()
    return {"id": str(response.id)}


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
def record_event(payload: UsageEventCreate, db: Database, principal: CurrentPrincipal):
    preferences = get_preferences(db, principal.subject)
    if not preferences.analytics_opt_in:
        raise HTTPException(status_code=403, detail="Usage analytics are not enabled")
    event = UsageEvent(
        anonymous_id=payload.anonymous_id,
        event_name=payload.event_name,
        properties_json=payload.properties,
    )
    db.add(event)
    db.commit()
    return {"accepted": True}


@router.get("/flags", response_model=list[FlagEvaluation])
def evaluate_flags(
    db: Database, principal: CurrentPrincipal, anonymous_id: str | None = None
):
    preferences = get_preferences(db, principal.subject)
    subject = anonymous_id or principal.subject
    flags = db.scalars(select(FeatureFlag).order_by(FeatureFlag.key)).all()
    return [
        FlagEvaluation(
            key=flag.key,
            enabled=flag_enabled(flag, subject, preferences.enrolled),
            config=flag.config_json,
        )
        for flag in flags
    ]


@router.get("/admin/feedback", response_model=list[FeedbackRead])
def admin_feedback(db: Database, _: AdminPrincipal):
    return db.scalars(select(FeedbackItem).order_by(FeedbackItem.created_at.desc())).all()


@router.patch("/admin/feedback/{feedback_id}", response_model=FeedbackRead)
def update_feedback(
    feedback_id: UUID, payload: FeedbackUpdate, db: Database, _: AdminPrincipal
):
    item = find_feedback(db, feedback_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return item


@router.get("/admin/health", response_model=ProductHealth)
def health(db: Database, _: AdminPrincipal):
    return product_health(db)


@router.get("/admin/flags", response_model=list[FeatureFlagRead])
def list_flags(db: Database, _: AdminPrincipal):
    return db.scalars(select(FeatureFlag).order_by(FeatureFlag.key)).all()


@router.post("/admin/flags", response_model=FeatureFlagRead, status_code=201)
def create_flag(payload: FeatureFlagCreate, db: Database, _: AdminPrincipal):
    if db.scalar(select(FeatureFlag).where(FeatureFlag.key == payload.key)):
        raise HTTPException(status_code=409, detail="Feature flag already exists")
    data = payload.model_dump()
    config = data.pop("config")
    flag = FeatureFlag(**data, config_json=config)
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag

