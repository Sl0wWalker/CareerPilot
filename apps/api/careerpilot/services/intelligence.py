from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models.enterprise import AgentRun, EnterprisePolicy
from careerpilot.models.intelligence import (
    AutonomousAgentConfig,
    CareerStrategy,
    MarketInsight,
    OpportunityMonitor,
    SkillForecast,
)
from careerpilot.models.jobs import Job
from careerpilot.models.tracking import Application, Contact
from careerpilot.schemas.intelligence import IntelligenceOverview

SAFE_CAPABILITIES = {
    "jobs.search",
    "jobs.read",
    "matching.analyze",
    "documents.prepare",
    "profile.read",
    "notifications.create",
    "marketplace.workflow.run",
}
EXTERNAL_ACTIONS = {"applications.submit", "messages.send", "profile.write", "documents.publish"}


def validate_agent_config(config) -> None:
    unknown = set(config.capabilities) - SAFE_CAPABILITIES - EXTERNAL_ACTIONS
    if unknown:
        raise ValueError(f"Unsupported capabilities: {', '.join(sorted(unknown))}")
    if config.autonomy_level == "execute":
        for action in set(config.capabilities) & EXTERNAL_ACTIONS:
            if config.approval_policy.get(action, "always") != "always":
                raise ValueError(f"{action} must always require explicit approval")


def forecast_trend(current: float, projected: float) -> str:
    change = projected - current
    if change >= 0.1:
        return "rising"
    if change <= -0.1:
        return "declining"
    return "stable"


def governance_snapshot(db: Session, owner_id: str) -> dict:
    policies = db.scalars(
        select(EnterprisePolicy).where(EnterprisePolicy.key.like("agents.%"))
    ).all()
    agents = db.scalars(
        select(AutonomousAgentConfig).where(AutonomousAgentConfig.owner_id == owner_id)
    ).all()
    return {
        "human_review_default": True,
        "external_actions_always_gated": sorted(EXTERNAL_ACTIONS),
        "configured_policies": [
            {"key": policy.key, "value": policy.value, "enforcement": policy.enforcement}
            for policy in policies
        ],
        "agents": [
            {
                "agent_key": agent.agent_key,
                "autonomy_level": agent.autonomy_level,
                "enabled": agent.enabled,
                "approval_policy": agent.approval_policy,
            }
            for agent in agents
        ],
    }


def overview(db: Session, owner_id: str) -> IntelligenceOverview:
    forecasts = db.scalars(
        select(SkillForecast)
        .where(SkillForecast.owner_id == owner_id, SkillForecast.trend == "rising")
        .order_by(SkillForecast.projected_demand.desc())
        .limit(8)
    ).all()
    insights = db.scalars(
        select(MarketInsight)
        .where(MarketInsight.owner_id == owner_id)
        .order_by(MarketInsight.created_at.desc())
        .limit(6)
    ).all()
    applications = db.scalar(select(func.count(Application.id))) or 0
    contacts = db.scalar(select(func.count(Contact.id))) or 0
    jobs = db.scalar(select(func.count(Job.id))) or 0
    return IntelligenceOverview(
        strategies=db.scalar(
            select(func.count(CareerStrategy.id)).where(CareerStrategy.owner_id == owner_id)
        )
        or 0,
        active_monitors=db.scalar(
            select(func.count(OpportunityMonitor.id)).where(
                OpportunityMonitor.owner_id == owner_id, OpportunityMonitor.enabled.is_(True)
            )
        )
        or 0,
        configured_agents=db.scalar(
            select(func.count(AutonomousAgentConfig.id)).where(
                AutonomousAgentConfig.owner_id == owner_id
            )
        )
        or 0,
        enabled_agents=db.scalar(
            select(func.count(AutonomousAgentConfig.id)).where(
                AutonomousAgentConfig.owner_id == owner_id,
                AutonomousAgentConfig.enabled.is_(True),
            )
        )
        or 0,
        approval_required_agents=db.scalar(
            select(func.count(AutonomousAgentConfig.id)).where(
                AutonomousAgentConfig.owner_id == owner_id,
                AutonomousAgentConfig.autonomy_level.in_(["prepare", "execute"]),
            )
        )
        or 0,
        rising_skills=[
            {
                "skill": item.skill,
                "current_demand": item.current_demand,
                "projected_demand": item.projected_demand,
                "confidence": item.confidence,
            }
            for item in forecasts
        ],
        market_insights=[
            {
                "id": str(item.id),
                "type": item.insight_type,
                "title": item.title,
                "summary": item.summary,
                "confidence": item.confidence,
            }
            for item in insights
        ],
        recruiter_engagement={
            "known_contacts": contacts,
            "applications": applications,
            "contact_coverage": round(contacts / applications, 3) if applications else 0.0,
        },
        opportunity_pipeline={
            "indexed_jobs": jobs,
            "agent_runs": db.scalar(select(func.count(AgentRun.id))) or 0,
            "applications": applications,
        },
    )

