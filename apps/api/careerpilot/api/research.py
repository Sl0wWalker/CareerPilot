from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.core.security import Principal, current_principal
from careerpilot.db.session import get_db
from careerpilot.models.research import (
    EvaluationDataset,
    ExperimentRun,
    IncubatedFeature,
    ResearchExperiment,
)
from careerpilot.schemas.research import (
    DatasetCreate,
    ExperimentCreate,
    ExperimentRead,
    ExperimentRunCreate,
    ExperimentStateUpdate,
    FeatureCreate,
    PromotionRequest,
)
from careerpilot.services.research import benchmark_summary, evaluate_run, promotion_decision

router = APIRouter(prefix="/api/v1/research", tags=["innovation-lab"])
Database = Annotated[Session, Depends(get_db)]
User = Annotated[Principal, Depends(current_principal)]


@router.get("/experiments", response_model=list[ExperimentRead])
def list_experiments(db: Database, principal: User):
    return db.scalars(
        select(ResearchExperiment)
        .where(ResearchExperiment.owner_id == principal.subject)
        .order_by(ResearchExperiment.created_at.desc())
    ).all()


@router.post("/experiments", response_model=ExperimentRead, status_code=201)
def create_experiment(payload: ExperimentCreate, db: Database, principal: User):
    existing = db.scalar(
        select(ResearchExperiment).where(
            ResearchExperiment.owner_id == principal.subject,
            ResearchExperiment.slug == payload.slug,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Experiment slug already exists")
    item = ResearchExperiment(owner_id=principal.subject, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/experiments/{experiment_id}", response_model=ExperimentRead)
def update_experiment(
    experiment_id: UUID, payload: ExperimentStateUpdate, db: Database, principal: User
):
    item = db.scalar(
        select(ResearchExperiment).where(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.owner_id == principal.subject,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.post("/datasets", status_code=201)
def create_dataset(payload: DatasetCreate, db: Database, principal: User):
    item = EvaluationDataset(owner_id=principal.subject, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "version": item.version, "modality": item.modality}


@router.post("/experiments/{experiment_id}/runs", status_code=201)
def record_run(
    experiment_id: UUID, payload: ExperimentRunCreate, db: Database, principal: User
):
    experiment = db.scalar(
        select(ResearchExperiment).where(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.owner_id == principal.subject,
        )
    )
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    evaluation = evaluate_run(
        payload.metrics, payload.safety_results, experiment.success_criteria
    )
    run = ExperimentRun(
        owner_id=principal.subject,
        experiment_id=str(experiment.id),
        dataset_id=str(payload.dataset_id) if payload.dataset_id else None,
        model_provider=payload.model_provider,
        model_name=payload.model_name,
        status="completed",
        parameters=payload.parameters,
        metrics={**payload.metrics, "evaluation": evaluation},
        safety_results=payload.safety_results,
        latency_ms=payload.latency_ms,
        notes=payload.notes,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"id": run.id, "status": run.status, "evaluation": evaluation}


@router.get("/benchmarks")
def benchmarks(db: Database, principal: User):
    runs = db.scalars(
        select(ExperimentRun).where(ExperimentRun.owner_id == principal.subject)
    ).all()
    return benchmark_summary(runs)


@router.post("/incubator", status_code=201)
def create_feature(payload: FeatureCreate, db: Database, principal: User):
    item = IncubatedFeature(
        owner_id=principal.subject,
        **payload.model_dump(exclude={"experiment_id"}),
        experiment_id=str(payload.experiment_id) if payload.experiment_id else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "key": item.key, "stage": item.stage}


@router.post("/incubator/{feature_id}/promote")
def promote_feature(
    feature_id: UUID, payload: PromotionRequest, db: Database, principal: User
):
    feature = db.scalar(
        select(IncubatedFeature).where(
            IncubatedFeature.id == feature_id,
            IncubatedFeature.owner_id == principal.subject,
        )
    )
    if feature is None:
        raise HTTPException(status_code=404, detail="Incubated feature not found")
    runs = []
    if feature.experiment_id:
        records = db.scalars(
            select(ExperimentRun).where(
                ExperimentRun.owner_id == principal.subject,
                ExperimentRun.experiment_id == feature.experiment_id,
            )
        ).all()
        runs = [
            run.metrics.get("evaluation", {})
            for run in records
            if isinstance(run.metrics, dict)
        ]
    decision = promotion_decision(runs)
    if payload.target_stage == "production" and not decision["eligible"]:
        raise HTTPException(status_code=409, detail=decision["reason"])
    feature.stage = payload.target_stage
    feature.rollout_percentage = payload.rollout_percentage
    feature.safety_approved = decision["eligible"]
    feature.promotion_evidence = decision
    db.commit()
    return {"stage": feature.stage, "decision": decision}
