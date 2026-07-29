from datetime import date
from uuid import uuid4

from careerpilot.models import CareerProfile, DocumentVersion, Experience, Job, JobMatch, Skill
from careerpilot.services.documents import DocumentService


class MemoryDocuments:
    def __init__(self):
        self.values = []

    def next_version(self, *_args):
        return len(self.values) + 1

    def save(self, value):
        self.values.append(value)
        return value


def profile() -> CareerProfile:
    value = CareerProfile(id=uuid4(), first_name="A", last_name="Candidate")
    value.skills = [Skill(id=uuid4(), profile_id=value.id, name="Python")]
    value.experiences = [
        Experience(
            id=uuid4(),
            profile_id=value.id,
            company="Example",
            title="Engineer",
            start_date=date(2020, 1, 1),
            description="Built Python automation.",
        )
    ]
    value.projects = []
    value.education = []
    value.achievements = []
    return value


def test_tailoring_uses_verified_facts_and_versions():
    repository = MemoryDocuments()
    candidate = profile()
    job = Job(
        id=uuid4(),
        company_id=uuid4(),
        source_provider="test",
        external_id="1",
        title="Python Engineer",
        description="Python automation",
        canonical_url="https://example.test/job",
        fingerprint="a" * 64,
        search_text="python",
    )
    match = JobMatch(
        id=uuid4(),
        job_id=job.id,
        profile_id=candidate.id,
        overall_score=90,
        confidence=0.9,
        recommendation="strong_match",
        engine_version="1",
        components={},
        strengths=["Matched skill: python"],
        gaps=[],
        hard_blocks=[],
        reasons=[],
        evidence=[{"type": "skill", "id": str(candidate.skills[0].id), "text": "python"}],
    )
    result = DocumentService(repository).tailor_resume(
        candidate, job, match, use_ai=False
    )
    assert result.version == 1
    assert result.content["skills"] == ["Python"]
    assert result.keyword_coverage["matched"] == ["python"]
    assert result.status == "draft"


def test_sensitive_screening_answer_requires_review():
    repository = MemoryDocuments()
    repository.save_answers = lambda values: values
    candidate = profile()
    job = type("JobContext", (), {"id": uuid4()})()
    result = DocumentService(repository).screening(
        candidate, job, ["Will you require sponsorship?"], use_ai=False
    )
    assert result[0].sensitive is True
    assert result[0].answer is None
    assert result[0].status == "needs_review"


def test_exports_are_valid_container_formats():
    value = DocumentVersion(
        id=uuid4(),
        profile_id=uuid4(),
        document_type="resume",
        version=1,
        title="Candidate",
        content={"summary": "Engineer"},
        evidence=[],
        keyword_coverage={},
    )
    service = DocumentService(MemoryDocuments())
    assert service.export(value, "pdf").startswith(b"%PDF")
    assert service.export(value, "docx").startswith(b"PK")
