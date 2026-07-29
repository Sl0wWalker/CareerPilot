from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, require_role
from careerpilot.db.session import get_db
from careerpilot.models.enterprise import (
    AgentMemory,
    AgentRun,
    AuditEvent,
    EnterprisePolicy,
    Membership,
    Organization,
    SSOConnection,
    UsageQuota,
    Workspace,
)
from careerpilot.schemas.enterprise import (
    AgentMemoryUpsert,
    AgentRunCreate,
    AgentRunRead,
    EnterpriseOverview,
    MembershipCreate,
    MembershipRead,
    OrganizationCreate,
    OrganizationRead,
    PolicyUpsert,
    QuotaUpsert,
    SSOConnectionUpsert,
    WorkspaceCreate,
    WorkspaceRead,
)
from careerpilot.services.enterprise import consume_quota, overview, record_audit
from careerpilot.services.platform import PlatformEvent, event_bus

router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])
Database = Annotated[Session, Depends(get_db)]
AdminPrincipal = Annotated[Principal, Depends(require_role("owner", "admin"))]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Enterprise resource already exists") from exc


def _organization(db: Session, organization_id: UUID) -> Organization:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.get("/overview", response_model=EnterpriseOverview)
def enterprise_overview(db: Database, _: AdminPrincipal):
    return overview(db)


@router.get("/organizations", response_model=list[OrganizationRead])
def list_organizations(db: Database, _: AdminPrincipal):
    return db.scalars(select(Organization).order_by(Organization.name)).all()


@router.post("/organizations", response_model=OrganizationRead, status_code=201)
async def create_organization(payload: OrganizationCreate, db: Database, principal: AdminPrincipal):
    organization = Organization(name=payload.name, slug=payload.slug)
    db.add(organization)
    db.flush()
    db.add(
        Membership(
            organization_id=organization.id,
            subject=principal.subject,
            role="owner",
            permissions=["*"],
        )
    )
    record_audit(
        db,
        organization.id,
        principal.subject,
        "organization.created",
        "organization",
        str(organization.id),
    )
    _commit(db)
    db.refresh(organization)
    await event_bus.publish(
        PlatformEvent("enterprise.organization.created", {"id": str(organization.id)})
    )
    return organization


@router.post(
    "/organizations/{organization_id}/workspaces",
    response_model=WorkspaceRead,
    status_code=201,
)
def create_workspace(
    organization_id: UUID,
    payload: WorkspaceCreate,
    db: Database,
    principal: AdminPrincipal,
):
    _organization(db, organization_id)
    workspace = Workspace(organization_id=organization_id, **payload.model_dump())
    db.add(workspace)
    db.flush()
    record_audit(
        db,
        organization_id,
        principal.subject,
        "workspace.created",
        "workspace",
        str(workspace.id),
    )
    _commit(db)
    db.refresh(workspace)
    return workspace


@router.get("/organizations/{organization_id}/members", response_model=list[MembershipRead])
def list_members(organization_id: UUID, db: Database, _: AdminPrincipal):
    _organization(db, organization_id)
    return db.scalars(select(Membership).where(Membership.organization_id == organization_id)).all()


@router.post(
    "/organizations/{organization_id}/members",
    response_model=MembershipRead,
    status_code=201,
)
def add_member(
    organization_id: UUID,
    payload: MembershipCreate,
    db: Database,
    principal: AdminPrincipal,
):
    _organization(db, organization_id)
    membership = Membership(organization_id=organization_id, **payload.model_dump())
    db.add(membership)
    db.flush()
    record_audit(
        db,
        organization_id,
        principal.subject,
        "membership.created",
        "membership",
        str(membership.id),
        {"role": membership.role},
    )
    _commit(db)
    db.refresh(membership)
    return membership


@router.put("/organizations/{organization_id}/sso")
def configure_sso(
    organization_id: UUID,
    payload: SSOConnectionUpsert,
    db: Database,
    principal: AdminPrincipal,
):
    _organization(db, organization_id)
    connection = db.scalar(
        select(SSOConnection).where(SSOConnection.organization_id == organization_id)
    )
    if connection is None:
        connection = SSOConnection(organization_id=organization_id, **payload.model_dump())
        db.add(connection)
    else:
        for key, value in payload.model_dump().items():
            setattr(connection, key, value)
    record_audit(db, organization_id, principal.subject, "sso.configured", "sso")
    _commit(db)
    return {"configured": True, "protocol": connection.protocol, "enabled": connection.enabled}


@router.put("/organizations/{organization_id}/policies")
def upsert_policy(
    organization_id: UUID, payload: PolicyUpsert, db: Database, principal: AdminPrincipal
):
    _organization(db, organization_id)
    policy = db.scalar(
        select(EnterprisePolicy).where(
            EnterprisePolicy.organization_id == organization_id,
            EnterprisePolicy.key == payload.key,
        )
    )
    if policy is None:
        policy = EnterprisePolicy(organization_id=organization_id, **payload.model_dump())
        db.add(policy)
    else:
        policy.value = payload.value
        policy.enforcement = payload.enforcement
    record_audit(db, organization_id, principal.subject, "policy.updated", "policy", payload.key)
    _commit(db)
    return {"key": policy.key, "value": policy.value, "enforcement": policy.enforcement}


@router.put("/organizations/{organization_id}/quotas")
def upsert_quota(
    organization_id: UUID, payload: QuotaUpsert, db: Database, principal: AdminPrincipal
):
    _organization(db, organization_id)
    quota = db.scalar(
        select(UsageQuota).where(
            UsageQuota.organization_id == organization_id, UsageQuota.metric == payload.metric
        )
    )
    if quota is None:
        quota = UsageQuota(organization_id=organization_id, **payload.model_dump())
        db.add(quota)
    else:
        quota.limit = payload.limit
    _commit(db)
    return {"metric": quota.metric, "limit": quota.limit, "used": quota.used}


@router.post(
    "/organizations/{organization_id}/agents",
    response_model=AgentRunRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def queue_agent(
    organization_id: UUID,
    payload: AgentRunCreate,
    db: Database,
    principal: AdminPrincipal,
):
    _organization(db, organization_id)
    try:
        consume_quota(db, organization_id, "agent_runs", 1)
    except ValueError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    run = AgentRun(organization_id=organization_id, **payload.model_dump())
    db.add(run)
    db.flush()
    record_audit(
        db,
        organization_id,
        principal.subject,
        "agent.queued",
        "agent_run",
        str(run.id),
        {"agent_type": run.agent_type},
    )
    _commit(db)
    db.refresh(run)
    await event_bus.publish(
        PlatformEvent("enterprise.agent.queued", {"id": str(run.id), "type": run.agent_type})
    )
    return run


@router.get("/organizations/{organization_id}/agents", response_model=list[AgentRunRead])
def list_agents(organization_id: UUID, db: Database, _: AdminPrincipal):
    _organization(db, organization_id)
    return db.scalars(
        select(AgentRun)
        .where(AgentRun.organization_id == organization_id)
        .order_by(AgentRun.created_at.desc())
    ).all()


@router.put("/organizations/{organization_id}/agent-memory")
def upsert_agent_memory(
    organization_id: UUID,
    payload: AgentMemoryUpsert,
    db: Database,
    _: AdminPrincipal,
):
    _organization(db, organization_id)
    memory = db.scalar(
        select(AgentMemory).where(
            AgentMemory.organization_id == organization_id,
            AgentMemory.namespace == payload.namespace,
            AgentMemory.key == payload.key,
        )
    )
    if memory is None:
        memory = AgentMemory(organization_id=organization_id, **payload.model_dump())
        db.add(memory)
    else:
        memory.value = payload.value
    _commit(db)
    return {"namespace": memory.namespace, "key": memory.key, "value": memory.value}


@router.get("/organizations/{organization_id}/audit")
def audit_log(organization_id: UUID, db: Database, _: AdminPrincipal):
    _organization(db, organization_id)
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.organization_id == organization_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(200)
    ).all()
    return [
        {
            "id": event.id,
            "actor": event.actor,
            "action": event.action,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]
