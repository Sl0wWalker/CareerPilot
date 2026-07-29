import hashlib
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models.beta import (
    BetaPreference,
    FeatureFlag,
    FeedbackItem,
    SatisfactionResponse,
    UsageEvent,
)
from careerpilot.schemas.beta import ProductHealth


def get_preferences(db: Session, user_id: str) -> BetaPreference:
    preferences = db.scalar(select(BetaPreference).where(BetaPreference.user_id == user_id))
    if preferences is None:
        preferences = BetaPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


def flag_enabled(flag: FeatureFlag, subject: str, beta_member: bool) -> bool:
    if not flag.enabled or (flag.beta_only and not beta_member):
        return False
    bucket = int(hashlib.sha256(f"{flag.key}:{subject}".encode()).hexdigest()[:8], 16) % 100
    return bucket < flag.rollout_percentage


def product_health(db: Session) -> ProductHealth:
    feedback_total = db.scalar(select(func.count(FeedbackItem.id))) or 0
    open_bugs = (
        db.scalar(
            select(func.count(FeedbackItem.id)).where(
                FeedbackItem.kind == "bug", FeedbackItem.status.not_in(("resolved", "closed"))
            )
        )
        or 0
    )
    features = (
        db.scalar(select(func.count(FeedbackItem.id)).where(FeedbackItem.kind == "feature")) or 0
    )
    average = db.scalar(select(func.avg(SatisfactionResponse.score)))
    opted_in = (
        db.scalar(
            select(func.count(BetaPreference.id)).where(BetaPreference.analytics_opt_in.is_(True))
        )
        or 0
    )
    events = db.scalar(select(func.count(UsageEvent.id))) or 0
    return ProductHealth(
        feedback_total=feedback_total,
        open_bugs=open_bugs,
        feature_requests=features,
        satisfaction_average=round(float(average), 2) if average is not None else None,
        opted_in_users=opted_in,
        usage_events=events,
    )


def find_feedback(db: Session, feedback_id: UUID) -> FeedbackItem | None:
    return db.get(FeedbackItem, feedback_id)

