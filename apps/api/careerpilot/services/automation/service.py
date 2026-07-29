import re
from typing import Any

from careerpilot.models import CareerProfile, DocumentVersion, ScreeningAnswer
from careerpilot.models.automation import AutomationRun
from careerpilot.repositories.automation import AutomationRepository
from careerpilot.services.automation.adapters import adapter_for_url

SENSITIVE = ("sponsor", "authorization", "salary", "gender", "race", "veteran",
             "disability", "criminal", "clearance", "signature")


class AutomationService:
    def __init__(self, repository: AutomationRepository) -> None:
        self.repository = repository

    def create(self, profile: CareerProfile, job_id, resume: DocumentVersion,
               application_url: str, cover_letter_id=None, dry_run=True, max_attempts=3):
        if resume.status != "approved":
            raise ValueError("resume must be approved before automation")
        adapter = adapter_for_url(application_url)
        run = AutomationRun(
            profile_id=profile.id, job_id=job_id, resume_id=resume.id,
            cover_letter_id=cover_letter_id, adapter=adapter.name,
            application_url=application_url, dry_run=dry_run, max_attempts=max_attempts,
        )
        value = self.repository.save_run(run)
        self.repository.add_step(value.id, "created", "complete", adapter=adapter.name)
        return value

    def inspect(self, run: AutomationRun, profile: CareerProfile,
                fields: list[dict[str, Any]], answers: list[ScreeningAnswer]):
        mapped = [self._map(field, profile, answers) for field in fields]
        errors = [
            f"Required field needs review: {item['label']}"
            for item, source in zip(fields, mapped, strict=True)
            if item.get("required") and (source["value"] is None or source["requires_review"])
        ]
        run.field_snapshot = mapped
        run.validation_errors = errors
        run.checkpoint = "fields_mapped"
        needs_review = errors or any(x["requires_review"] for x in mapped)
        run.status = "needs_review" if needs_review else "ready"
        self.repository.add_step(run.id, "field_mapping", "complete", field_count=len(mapped))
        return self.repository.save_run(run), mapped

    def approve(self, run: AutomationRun, approved: bool):
        if not approved:
            run.status = "cancelled"
            run.approved = False
        else:
            if run.validation_errors:
                raise ValueError("resolve validation errors before approval")
            run.approved = True
            run.status = "ready"
            run.checkpoint = "user_approved"
        self.repository.add_step(run.id, "human_approval", "complete", approved=approved)
        return self.repository.save_run(run)

    def execute(self, run: AutomationRun):
        if not run.approved:
            raise ValueError("human approval is required before execution")
        if run.validation_errors:
            raise ValueError("validation errors must be resolved before execution")
        run.attempt_count += 1
        if run.attempt_count > run.max_attempts:
            raise ValueError("maximum retry count exceeded")
        # Browser execution deliberately stops at final review. Real page interaction is
        # delegated to Playwright adapters; dry-run is the safe default and test path.
        run.checkpoint = "ready_for_submission"
        run.status = "dry_run_complete" if run.dry_run else "running"
        self.repository.add_step(
            run.id, "browser_execution", "complete",
            dry_run=run.dry_run, stopped_before_submit=True,
        )
        return self.repository.save_run(run)

    @staticmethod
    def _map(field: dict[str, Any], profile: CareerProfile,
             answers: list[ScreeningAnswer]) -> dict[str, Any]:
        label = field["label"]
        key = re.sub(r"\W+", " ", label.casefold()).strip()
        known = {
            "first name": profile.first_name, "last name": profile.last_name,
            "full name": f"{profile.first_name} {profile.last_name}",
            "email": profile.email, "phone": profile.phone,
            "city": profile.city, "state": profile.region, "country": profile.country,
            "linkedin": profile.linkedin_url, "portfolio": profile.portfolio_url,
        }
        matched_key = next((name for name in known if name in key), None)
        sensitive = any(term in key for term in SENSITIVE)
        value = known.get(matched_key) if matched_key else None
        source = "profile" if matched_key else "unresolved"
        confidence = 0.98 if matched_key else 0.0
        if value is None:
            answer = next((item for item in answers if item.normalized_question == key
                           and item.status == "approved"), None)
            if answer:
                value, source, confidence = answer.answer, "approved_answer", answer.confidence
        return {
            "label": label, "value": value, "source": source, "confidence": confidence,
            "sensitive": sensitive, "requires_review": sensitive or value is None,
        }
