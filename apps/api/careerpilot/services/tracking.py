from datetime import UTC, datetime
from statistics import mean

from careerpilot.models.tracking import Application
from careerpilot.repositories.tracking import TrackingRepository

CLOSED = {"offer", "rejected", "withdrawn", "archived"}
RESPONDED = {"recruiter_screen", "interview", "offer", "rejected"}


class TrackingService:
    def __init__(self, repository: TrackingRepository) -> None:
        self.repository = repository

    def create(self, profile_id, payload) -> Application:
        value = Application(profile_id=profile_id, **payload)
        if value.status == "submitted":
            value.applied_at = datetime.now(UTC)
        value = self.repository.save(value)
        self.repository.event(value, "created", "Application created", to_status=value.status)
        return value

    def update(self, value: Application, changes: dict) -> Application:
        old_status = value.status
        new_status = changes.get("status")
        for key, item in changes.items():
            setattr(value, key, item)
        now = datetime.now(UTC)
        if new_status == "submitted" and value.applied_at is None:
            value.applied_at = now
        if new_status in RESPONDED and value.responded_at is None:
            value.responded_at = now
        if new_status in CLOSED:
            value.closed_at = now
        value = self.repository.save(value)
        if new_status and new_status != old_status:
            self.repository.event(
                value, "status_changed", f"Moved to {new_status.replace('_', ' ')}",
                from_status=old_status, to_status=new_status,
            )
        else:
            self.repository.event(value, "updated", "Application details updated")
        return value

    def analytics(self, applications: list[Application]) -> dict:
        by_status: dict[str, int] = {}
        for item in applications:
            by_status[item.status] = by_status.get(item.status, 0) + 1
        submitted = sum(item.applied_at is not None for item in applications)
        responses = sum(item.responded_at is not None for item in applications)
        interviews = sum(item.status in {"interview", "offer"} for item in applications)
        offers = sum(item.status == "offer" or item.outcome == "offer" for item in applications)
        rejections = sum(item.status == "rejected" or item.outcome == "rejected"
                         for item in applications)
        response_days = [
            (item.responded_at - item.applied_at).total_seconds() / 86400
            for item in applications if item.responded_at and item.applied_at
        ]
        def rate(count: int) -> float:
            return round(count / submitted * 100, 1) if submitted else 0.0
        return {
            "total": len(applications), "by_status": by_status, "submitted": submitted,
            "responses": responses, "interviews": interviews, "offers": offers,
            "rejections": rejections, "response_rate": rate(responses),
            "interview_rate": rate(interviews), "offer_rate": rate(offers),
            "average_days_to_response": round(mean(response_days), 1) if response_days else None,
        }
