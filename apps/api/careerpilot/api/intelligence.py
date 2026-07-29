from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal
from careerpilot.db.session import get_db
from careerpilot.models.intelligence import (
    AutonomousAgentConfig,
    CareerStrategy,
    NotificationChannel,
    OpportunityMonitor,
    SkillForecast,
)
from careerpilot.schemas.intelligence import (
    AgentConfigRead,
    AgentConfigUpsert,
    ForecastCreate,
    IntelligenceOverview,
    MonitorCreate,
    MonitorRead,
    NotificationCreate,
    StrategyCreate,
    StrategyRead,
)
from careerpilot.services.intelligence import (
    forecast_trend,
    governance_snapshot,
    overview,
    validate_agent_config,
)
from careerpilot.services.platform import PlatformEvent, event_bus

router = APIRouter(prefix="/api/v1/intelligence", tags=["career-intelligence"])
Database = Annotated[Session, Depends(get_db)]
User = Annotated[Principal, Depends(current_principal)]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Intelligence resource already exists") from exc


@router.get("/overview", response_model=IntelligenceOverview)
def intelligence_overview(db: Database, principal: User):
    return overview(db, principal.subject)


@router.get("/strategies", response_model=list[StrategyRead])
def list_strategies(db: Database, principal: User):
    return db.scalars(
        select(CareerStrategy)
        .where(CareerStrategy.owner_id == principal.subject)
        .order_by(CareerStrategy.created_at.desc())
    ).all()


@router.post("/strategies", response_model=StrategyRead, status_code=201)
def create_strategy(payload: StrategyCreate, db: Database, principal: User):
    strategy = CareerStrategy(owner_id=principal.subject, **payload.model_dump())
    db.add(strategy)
    _commit(db)
    db.refresh(strategy)
    return strategy


@router.get("/monitors", response_model=list[MonitorRead])
def list_monitors(db: Database, principal: User):
    return db.scalars(
        select(OpportunityMonitor)
        .where(OpportunityMonitor.owner_id == principal.subject)
        .order_by(OpportunityMonitor.created_at.desc())
    ).all()


@router.post("/monitors", response_model=MonitorRead, status_code=201)
async def create_monitor(payload: MonitorCreate, db: Database, principal: User):
    monitor = OpportunityMonitor(owner_id=principal.subject, **payload.model_dump())
    db.add(monitor)
    _commit(db)
    db.refresh(monitor)
    await event_bus.publish(
        PlatformEvent("intelligence.monitor.created", {"id": str(monitor.id)})
    )
    return monitor


@router.post("/monitors/{monitor_id}/run")
async def run_monitor(monitor_id: UUID, db: Database, principal: User):
    monitor = db.scalar(
        select(OpportunityMonitor).where(
            OpportunityMonitor.id == monitor_id,
            OpportunityMonitor.owner_id == principal.subject,
        )
    )
    if monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")
    monitor.last_result = {
        "status": "queued",
        "criteria": monitor.criteria,
        "approval_required_for_external_actions": True,
    }
    _commit(db)
    await event_bus.publish(
        PlatformEvent("intelligence.monitor.queued", {"id": str(monitor.id)})
    )
    return monitor.last_result


@router.get("/agents", response_model=list[AgentConfigRead])
def list_agent_configs(db: Database, principal: User):
    return db.scalars(
        select(AutonomousAgentConfig)
        .where(AutonomousAgentConfig.owner_id == principal.subject)
        .order_by(AutonomousAgentConfig.display_name)
    ).all()


@router.put("/agents/{agent_key}", response_model=AgentConfigRead)
def upsert_agent(
    agent_key: str, payload: AgentConfigUpsert, db: Database, principal: User
):
    if agent_key != payload.agent_key:
        raise HTTPException(status_code=422, detail="Agent key does not match path")
    try:
        validate_agent_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    agent = db.scalar(
        select(AutonomousAgentConfig).where(
            AutonomousAgentConfig.owner_id == principal.subject,
            AutonomousAgentConfig.agent_key == agent_key,
        )
    )
    if agent is None:
        agent = AutonomousAgentConfig(owner_id=principal.subject, **payload.model_dump())
        db.add(agent)
    else:
        for key, value in payload.model_dump().items():
            setattr(agent, key, value)
    _commit(db)
    db.refresh(agent)
    return agent


@router.put("/forecasts/{skill}")
def upsert_forecast(skill: str, payload: ForecastCreate, db: Database, principal: User):
    if skill.casefold() != payload.skill.casefold():
        raise HTTPException(status_code=422, detail="Skill does not match path")
    forecast = db.scalar(
        select(SkillForecast).where(
            SkillForecast.owner_id == principal.subject,
            SkillForecast.skill == payload.skill,
        )
    )
    values = payload.model_dump()
    values["trend"] = forecast_trend(payload.current_demand, payload.projected_demand)
    if forecast is None:
        forecast = SkillForecast(owner_id=principal.subject, **values)
        db.add(forecast)
    else:
        for key, value in values.items():
            setattr(forecast, key, value)
    _commit(db)
    return {"skill": forecast.skill, "trend": forecast.trend, "confidence": forecast.confidence}


@router.post("/notifications", status_code=201)
def create_notification_channel(payload: NotificationCreate, db: Database, principal: User):
    channel = NotificationChannel(owner_id=principal.subject, **payload.model_dump())
    db.add(channel)
    _commit(db)
    db.refresh(channel)
    return {
        "id": channel.id,
        "channel_type": channel.channel_type,
        "label": channel.label,
        "enabled": channel.enabled,
    }


@router.get("/governance")
def autonomy_governance(db: Database, principal: User):
    return governance_snapshot(db, principal.subject)

