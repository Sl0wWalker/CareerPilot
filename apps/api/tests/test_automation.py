from datetime import date
from uuid import uuid4

from careerpilot.models import CareerProfile, DocumentVersion, Experience, ScreeningAnswer
from careerpilot.models.automation import AutomationRun
from careerpilot.services.automation import AutomationService, adapter_for_url


class MemoryAutomation:
    def __init__(self):
        self.steps = []

    def save_run(self, value):
        self.value = value
        return value

    def add_step(self, run_id, name, status, **details):
        self.steps.append((run_id, name, status, details))


def candidate():
    profile = CareerProfile(
        id=uuid4(), first_name="Ada", last_name="Lovelace",
        email="ada@example.test", city="Austin",
    )
    profile.experiences = [
        Experience(
            id=uuid4(), profile_id=profile.id, company="Example", title="Engineer",
            start_date=date(2022, 1, 1),
        )
    ]
    return profile


def test_adapter_detection():
    assert adapter_for_url("https://boards.greenhouse.io/acme/jobs/1").name == "greenhouse"
    assert adapter_for_url("https://jobs.lever.co/acme/1").name == "lever"
    assert adapter_for_url("https://acme.myworkdayjobs.com/job").name == "workday"
    assert adapter_for_url("https://example.test/apply").name == "generic"


def test_create_requires_approved_resume():
    repository = MemoryAutomation()
    resume = DocumentVersion(
        id=uuid4(), profile_id=uuid4(), document_type="resume", version=1,
        status="draft", title="Resume", content={}, evidence=[], keyword_coverage={},
    )
    try:
        AutomationService(repository).create(
            candidate(), uuid4(), resume, "https://example.test/apply"
        )
    except ValueError as error:
        assert "approved" in str(error)
    else:
        raise AssertionError("draft resume was accepted")


def test_sensitive_and_unknown_fields_require_review():
    repository = MemoryAutomation()
    profile = candidate()
    run = AutomationRun(
        id=uuid4(), profile_id=profile.id, job_id=uuid4(), resume_id=uuid4(),
        adapter="greenhouse", application_url="https://boards.greenhouse.io/a/jobs/1",
        dry_run=True,
    )
    run, fields = AutomationService(repository).inspect(
        run, profile,
        [
            {"label": "Email", "required": True},
            {"label": "Will you require sponsorship?", "required": True},
        ],
        [],
    )
    assert fields[0]["value"] == "ada@example.test"
    assert fields[0]["requires_review"] is False
    assert fields[1]["sensitive"] is True
    assert run.status == "needs_review"
    assert run.validation_errors


def test_approved_answer_is_still_reviewed_when_sensitive():
    repository = MemoryAutomation()
    profile = candidate()
    job_id = uuid4()
    answer = ScreeningAnswer(
        id=uuid4(), profile_id=profile.id, job_id=job_id,
        question="Will you require sponsorship?",
        normalized_question="will you require sponsorship",
        answer="Yes", evidence=[], confidence=1.0, sensitive=True, status="approved",
    )
    run = AutomationRun(
        id=uuid4(), profile_id=profile.id, job_id=job_id, resume_id=uuid4(),
        adapter="generic", application_url="https://example.test", dry_run=True,
    )
    _, fields = AutomationService(repository).inspect(
        run, profile, [{"label": answer.question, "required": False}], [answer]
    )
    assert fields[0]["value"] == "Yes"
    assert fields[0]["requires_review"] is True


def test_execution_requires_human_approval():
    repository = MemoryAutomation()
    run = AutomationRun(
        id=uuid4(), profile_id=uuid4(), job_id=uuid4(), resume_id=uuid4(),
        adapter="generic", application_url="https://example.test", dry_run=True,
        approved=False, validation_errors=[],
    )
    try:
        AutomationService(repository).execute(run)
    except ValueError as error:
        assert "approval" in str(error)
    else:
        raise AssertionError("unapproved run executed")
