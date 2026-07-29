from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

PackageType = Literal[
    "prompt_pack", "resume_template", "workflow", "job_source", "plugin", "agent_pack"
]
Channel = Literal["stable", "beta", "canary"]


class PackagePublish(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,159}$")
    name: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=10, max_length=2000)
    package_type: PackageType
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?$")
    channel: Channel = "stable"
    manifest: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[dict[str, str]] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class PackageRead(PackagePublish):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    publisher_id: str
    signature: str
    published: bool
    rating: float
    rating_count: int
    created_at: datetime


class InstallationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    package_slug: str
    installed_version: str
    channel: str
    enabled: bool
    configuration: dict[str, Any]


class InstallRequest(BaseModel):
    channel: Channel = "stable"
    configuration: dict[str, Any] = Field(default_factory=dict)


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str = Field(default="", max_length=2000)


class WorkflowNode(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,120}$")
    type: Literal["action", "ai", "condition", "approval", "integration"]
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: str | None = None


class WorkflowGraph(BaseModel):
    nodes: list[WorkflowNode] = Field(min_length=1, max_length=100)
    edges: list[WorkflowEdge] = Field(default_factory=list, max_length=300)

    @model_validator(mode="after")
    def validate_graph(self):
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Workflow node IDs must be unique")
        known = set(ids)
        if any(edge.source not in known or edge.target not in known for edge in self.edges):
            raise ValueError("Workflow edges must reference existing nodes")
        return self


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    trigger_type: Literal["manual", "schedule", "event"] = "manual"
    graph: WorkflowGraph


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str
    version: int
    enabled: bool
    trigger_type: str
    graph: dict[str, Any]
    created_at: datetime


class ExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    status: str
    current_node: str | None
    context: dict[str, Any]
    output: dict[str, Any]
    error: str | None
