import hashlib
import json
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models.marketplace import (
    MarketplacePackage,
    PackageInstallation,
    PackageReview,
    WorkflowDefinition,
    WorkflowExecution,
)
from careerpilot.schemas.marketplace import PackagePublish, WorkflowGraph

ALLOWED_PERMISSIONS = {
    "ai.generate",
    "jobs.read",
    "jobs.search",
    "profile.read",
    "documents.read",
    "documents.write",
    "applications.read",
    "integrations.call",
}


def package_signature(payload: PackagePublish) -> str:
    canonical = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_package(payload: PackagePublish) -> None:
    unknown = sorted(set(payload.permissions) - ALLOWED_PERMISSIONS)
    if unknown:
        raise ValueError(f"Unsupported permissions: {', '.join(unknown)}")
    for dependency in payload.dependencies:
        if not dependency.get("slug") or not dependency.get("version"):
            raise ValueError("Dependencies require slug and version")


def install_package(
    db: Session,
    owner_id: str,
    package: MarketplacePackage,
    channel: str,
    configuration: dict[str, Any],
) -> PackageInstallation:
    if not package.published:
        raise ValueError("Only published packages can be installed")
    for dependency in package.dependencies:
        installed = db.scalar(
            select(PackageInstallation).where(
                PackageInstallation.owner_id == owner_id,
                PackageInstallation.package_slug == dependency["slug"],
                PackageInstallation.enabled.is_(True),
            )
        )
        if installed is None:
            raise ValueError(f"Missing dependency: {dependency['slug']}")
    record = db.scalar(
        select(PackageInstallation).where(
            PackageInstallation.owner_id == owner_id,
            PackageInstallation.package_slug == package.slug,
        )
    )
    if record is None:
        record = PackageInstallation(
            owner_id=owner_id,
            package_id=package.id,
            package_slug=package.slug,
            installed_version=package.version,
        )
        db.add(record)
    record.installed_version = package.version
    record.channel = channel
    record.configuration = configuration
    record.enabled = True
    db.commit()
    db.refresh(record)
    return record


def update_rating(db: Session, package: MarketplacePackage) -> None:
    rating, count = db.execute(
        select(func.avg(PackageReview.rating), func.count(PackageReview.id)).where(
            PackageReview.package_id == package.id
        )
    ).one()
    package.rating = float(rating or 0)
    package.rating_count = int(count)
    db.commit()


def validate_workflow(graph: WorkflowGraph) -> list[str]:
    warnings: list[str] = []
    incoming = {edge.target for edge in graph.edges}
    roots = [node for node in graph.nodes if node.id not in incoming]
    if len(roots) != 1:
        warnings.append("Workflow should have exactly one entry node")
    for node in graph.nodes:
        if node.type == "integration" and not node.config.get("connection"):
            warnings.append(f"Integration node {node.id} needs a connection")
        if node.type == "ai" and not node.config.get("prompt"):
            warnings.append(f"AI node {node.id} needs a prompt")
    return warnings


def execute_workflow(
    db: Session, workflow: WorkflowDefinition, owner_id: str, context: dict[str, Any]
) -> WorkflowExecution:
    graph = WorkflowGraph.model_validate(workflow.graph)
    execution = WorkflowExecution(
        workflow_id=workflow.id, owner_id=owner_id, status="running", context=context
    )
    db.add(execution)
    db.flush()
    output: dict[str, Any] = {}
    for node in graph.nodes:
        execution.current_node = node.id
        if node.type == "approval":
            execution.status = "awaiting_approval"
            output["approval"] = node.config.get("message", "Approval required")
            break
        if node.type == "condition":
            key = str(node.config.get("key", ""))
            output[node.id] = bool(_resolve(context, key))
        elif node.type == "ai":
            output[node.id] = {"status": "queued", "prompt": node.config.get("prompt", "")}
        else:
            output[node.id] = {"status": "completed", "sandboxed": True}
    else:
        execution.status = "completed"
        execution.current_node = None
    execution.output = output
    db.commit()
    db.refresh(execution)
    return execution


def _resolve(context: dict[str, Any], key: str) -> Any:
    value: Any = context
    for part in filter(None, re.split(r"\.", key)):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value
