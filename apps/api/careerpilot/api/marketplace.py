from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal, require_role
from careerpilot.db.session import get_db
from careerpilot.models.marketplace import (
    MarketplacePackage,
    PackageInstallation,
    PackageReview,
    WorkflowDefinition,
    WorkflowExecution,
)
from careerpilot.schemas.marketplace import (
    ExecutionRead,
    InstallationRead,
    InstallRequest,
    PackagePublish,
    PackageRead,
    ReviewCreate,
    WorkflowCreate,
    WorkflowRead,
)
from careerpilot.services.marketplace import (
    execute_workflow,
    install_package,
    package_signature,
    update_rating,
    validate_package,
    validate_workflow,
)
from careerpilot.services.platform import PlatformEvent, event_bus

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])
Database = Annotated[Session, Depends(get_db)]
PrincipalDep = Annotated[Principal, Depends(current_principal)]
Publisher = Annotated[Principal, Depends(require_role("owner", "admin", "publisher"))]


@router.get("/packages", response_model=list[PackageRead])
def list_packages(
    db: Database,
    _: PrincipalDep,
    query: str = "",
    package_type: str | None = None,
    channel: str = "stable",
):
    statement = select(MarketplacePackage).where(
        MarketplacePackage.published.is_(True), MarketplacePackage.channel == channel
    )
    if query:
        statement = statement.where(
            or_(
                MarketplacePackage.name.ilike(f"%{query}%"),
                MarketplacePackage.summary.ilike(f"%{query}%"),
            )
        )
    if package_type:
        statement = statement.where(MarketplacePackage.package_type == package_type)
    return db.scalars(statement.order_by(MarketplacePackage.rating.desc())).all()


@router.post("/packages", response_model=PackageRead, status_code=status.HTTP_201_CREATED)
def publish_package(payload: PackagePublish, db: Database, principal: Publisher):
    try:
        validate_package(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record = MarketplacePackage(
        publisher_id=principal.subject,
        **payload.model_dump(),
        signature=package_signature(payload),
        published=True,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/packages/{package_id}/install", response_model=InstallationRead)
async def install(package_id: UUID, payload: InstallRequest, db: Database, principal: PrincipalDep):
    package = db.get(MarketplacePackage, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    try:
        record = install_package(
            db, principal.subject, package, payload.channel, payload.configuration
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await event_bus.publish(PlatformEvent("marketplace.package.installed", {"slug": package.slug}))
    return record


@router.get("/installations", response_model=list[InstallationRead])
def installations(db: Database, principal: PrincipalDep):
    return db.scalars(
        select(PackageInstallation).where(PackageInstallation.owner_id == principal.subject)
    ).all()


@router.delete("/installations/{installation_id}", status_code=status.HTTP_204_NO_CONTENT)
def uninstall(installation_id: UUID, db: Database, principal: PrincipalDep):
    record = db.get(PackageInstallation, installation_id)
    if record is None or record.owner_id != principal.subject:
        raise HTTPException(status_code=404, detail="Installation not found")
    db.delete(record)
    db.commit()


@router.post("/packages/{package_id}/reviews", status_code=status.HTTP_201_CREATED)
def review_package(package_id: UUID, payload: ReviewCreate, db: Database, principal: PrincipalDep):
    package = db.get(MarketplacePackage, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    review = db.scalar(
        select(PackageReview).where(
            PackageReview.package_id == package_id,
            PackageReview.reviewer_id == principal.subject,
        )
    )
    if review is None:
        review = PackageReview(package_id=package_id, reviewer_id=principal.subject)
        db.add(review)
    review.rating = payload.rating
    review.body = payload.body
    db.commit()
    update_rating(db, package)
    return {"accepted": True}


@router.post("/workflows", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate, db: Database, principal: PrincipalDep):
    warnings = validate_workflow(payload.graph)
    if warnings:
        raise HTTPException(status_code=422, detail=warnings)
    record = WorkflowDefinition(
        owner_id=principal.subject,
        name=payload.name,
        description=payload.description,
        trigger_type=payload.trigger_type,
        graph=payload.graph.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/workflows", response_model=list[WorkflowRead])
def list_workflows(db: Database, principal: PrincipalDep):
    return db.scalars(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.owner_id == principal.subject)
        .order_by(WorkflowDefinition.updated_at.desc())
    ).all()


@router.post("/workflows/{workflow_id}/execute", response_model=ExecutionRead)
def run_workflow(
    workflow_id: UUID,
    db: Database,
    principal: PrincipalDep,
    context: dict = None,
    dry_run: bool = Query(default=True),
):
    workflow = db.get(WorkflowDefinition, workflow_id)
    if workflow is None or workflow.owner_id != principal.subject:
        raise HTTPException(status_code=404, detail="Workflow not found")
    safe_context = dict(context or {})
    safe_context["dry_run"] = dry_run
    return execute_workflow(db, workflow, principal.subject, safe_context)


@router.post("/executions/{execution_id}/approve", response_model=ExecutionRead)
def approve_execution(execution_id: UUID, db: Database, principal: PrincipalDep):
    execution = db.get(WorkflowExecution, execution_id)
    if execution is None or execution.owner_id != principal.subject:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Execution is not awaiting approval")
    execution.status = "completed"
    execution.current_node = None
    execution.output = {**execution.output, "approved_by": principal.subject}
    db.commit()
    db.refresh(execution)
    return execution
