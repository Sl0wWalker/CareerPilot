from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,79}$")


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    plan: str
    enabled: bool
    settings: dict[str, Any]
    created_at: datetime


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,79}$")


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    enabled: bool


class MembershipCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=160)
    role: Literal["owner", "admin", "manager", "member", "auditor"] = "member"
    permissions: list[str] = Field(default_factory=list)


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    subject: str
    role: str
    permissions: list[str]
    enabled: bool


class SSOConnectionUpsert(BaseModel):
    protocol: Literal["oidc", "saml"]
    issuer: str = Field(min_length=3, max_length=1000)
    client_id: str | None = Field(default=None, max_length=300)
    metadata_url: str | None = Field(default=None, max_length=1000)
    enabled: bool = False


class PolicyUpsert(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,119}$")
    value: dict[str, Any] = Field(default_factory=dict)
    enforcement: Literal["enforce", "warn", "disabled"] = "enforce"


class QuotaUpsert(BaseModel):
    metric: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,79}$")
    limit: int = Field(ge=0)


class AgentRunCreate(BaseModel):
    workspace_id: UUID | None = None
    agent_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,99}$")
    objective: str = Field(min_length=3, max_length=4000)
    parent_run_id: UUID | None = None
    input: dict[str, Any] = Field(default_factory=dict)


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    workspace_id: UUID | None
    agent_type: str
    objective: str
    status: str
    parent_run_id: UUID | None
    input: dict[str, Any]
    output: dict[str, Any]
    error: str | None
    created_at: datetime


class AgentMemoryUpsert(BaseModel):
    namespace: str = Field(min_length=1, max_length=120)
    key: str = Field(min_length=1, max_length=200)
    value: dict[str, Any]


class EnterpriseOverview(BaseModel):
    organizations: int
    workspaces: int
    members: int
    active_agents: int
    audit_events: int
    quota_utilization: dict[str, float]
    queue_backend: str
    tenancy_mode: str
