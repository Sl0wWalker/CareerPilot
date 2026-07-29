from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models.enterprise import (
    AgentRun,
    AuditEvent,
    Membership,
    Organization,
    UsageQuota,
    Workspace,
)
from careerpilot.schemas.enterprise import EnterpriseOverview

ROLE_PERMISSIONS = {
    "owner": {"*"},
    "admin": {"organization:manage", "workspace:manage", "agent:manage", "audit:read"},
    "manager": {"workspace:manage", "agent:manage", "usage:read"},
    "member": {"agent:run", "workspace:read"},
    "auditor": {"audit:read", "usage:read"},
}


def effective_permissions(membership: Membership) -> set[str]:
    return ROLE_PERMISSIONS.get(membership.role, set()) | set(membership.permissions)


def require_permission(membership: Membership, permission: str) -> None:
    permissions = effective_permissions(membership)
    if "*" not in permissions and permission not in permissions:
        raise PermissionError(f"Missing permission: {permission}")


def record_audit(
    db: Session,
    organization_id,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        organization_id=organization_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.add(event)
    return event


def consume_quota(db: Session, organization_id, metric: str, amount: int = 1) -> UsageQuota | None:
    quota = db.scalar(
        select(UsageQuota).where(
            UsageQuota.organization_id == organization_id, UsageQuota.metric == metric
        )
    )
    if quota is None:
        return None
    if quota.used + amount > quota.limit:
        raise ValueError(f"Quota exceeded for {metric}")
    quota.used += amount
    return quota


def overview(db: Session) -> EnterpriseOverview:
    quotas = db.scalars(select(UsageQuota)).all()
    return EnterpriseOverview(
        organizations=db.scalar(select(func.count(Organization.id))) or 0,
        workspaces=db.scalar(select(func.count(Workspace.id))) or 0,
        members=db.scalar(select(func.count(Membership.id))) or 0,
        active_agents=db.scalar(
            select(func.count(AgentRun.id)).where(AgentRun.status.in_(["queued", "running"]))
        )
        or 0,
        audit_events=db.scalar(select(func.count(AuditEvent.id))) or 0,
        quota_utilization={
            quota.metric: (quota.used / quota.limit if quota.limit else 0.0) for quota in quotas
        },
        queue_backend="database-local",
        tenancy_mode="organization-workspace",
    )
