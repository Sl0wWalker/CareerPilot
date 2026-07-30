"""Seed a fictional, submission-safe CareerPilot demonstration."""

from datetime import date
from hashlib import sha256

from careerpilot.db.session import SessionLocal
from careerpilot.models import (
    Application,
    AutomationRun,
    CareerProfile,
    Company,
    DocumentVersion,
    Education,
    Experience,
    Job,
    JobMatch,
    JobPreference,
    Project,
    Skill,
)
from sqlalchemy import select

DEMO_EMAIL = "jordan.taylor@example.test"


def main() -> None:
    with SessionLocal() as session:
        existing = session.scalar(
            select(CareerProfile).where(CareerProfile.email == DEMO_EMAIL)
        )
        if existing:
            print("Demo data already exists.")
            return
        if session.scalar(select(CareerProfile)) is not None:
            raise SystemExit(
                "A real profile already exists. Demo seeding stopped to protect your data."
            )

        profile = CareerProfile(
            first_name="Jordan",
            last_name="Taylor",
            email=DEMO_EMAIL,
            city="Austin",
            region="Texas",
            country="United States",
        )
        profile.experiences = [
            Experience(
                company="Example Semiconductor",
                title="Senior Verification Engineer",
                start_date=date(2021, 1, 1),
                is_current=True,
                location="Austin, Texas",
                description="Built Python and Tcl automation for formal verification workflows.",
            )
        ]
        profile.education = [
            Education(
                institution="Example University",
                degree="Bachelor of Engineering",
                field_of_study="Electrical Engineering",
                end_year=2020,
            )
        ]
        profile.projects = [
            Project(
                name="Verification Flow Dashboard",
                description="Local dashboard for verification run monitoring.",
            )
        ]
        profile.skills = [
            Skill(name=name, years_experience=4, proficiency="advanced")
            for name in ("Python", "Tcl", "SystemVerilog", "Formal Verification")
        ]
        profile.job_preference = JobPreference(
            target_roles="Formal Verification Engineer",
            preferred_locations="Austin, Texas",
            remote_ok=True,
            willing_to_relocate=False,
            requires_sponsorship=True,
        )
        session.add(profile)
        session.flush()

        company = Company(name="Fictional Silicon Labs")
        session.add(company)
        session.flush()
        description = (
            "Build formal verification and logic-equivalence flows using Python, Tcl, "
            "SystemVerilog, and automation. Hybrid role in Austin, Texas."
        )
        job = Job(
            company_id=company.id,
            source_provider="demo",
            external_id="demo-formal-verification-1",
            title="Formal Verification Engineer",
            description=description,
            canonical_url="https://example.test/jobs/formal-verification",
            application_url="https://example.test/apply/formal-verification",
            location_raw="Austin, Texas, United States",
            city="Austin",
            region="Texas",
            country="United States",
            workplace_type="hybrid",
            employment_type="full-time",
            salary_min=125000,
            salary_max=155000,
            salary_currency="USD",
            salary_period="year",
            fingerprint=sha256(description.encode()).hexdigest(),
            search_text=f"formal verification engineer {description}".lower(),
            raw_payload={"demo": True},
            is_favorite=True,
        )
        session.add(job)
        session.flush()

        match = JobMatch(
            job_id=job.id,
            profile_id=profile.id,
            overall_score=88,
            confidence=0.94,
            recommendation="strong_match",
            engine_version="demo-1",
            components={
                "skills": {"score": 92, "weight": 0.3, "weighted_score": 27.6,
                           "confidence": 0.95, "explanation": "Four verified skills match.",
                           "matched": ["Python", "Tcl", "SystemVerilog"],
                           "missing": []},
                "experience": {"score": 86, "weight": 0.2, "weighted_score": 17.2,
                               "confidence": 0.9, "explanation": "Relevant verified experience.",
                               "matched": ["Formal verification"], "missing": []},
            },
            strengths=["Python", "Tcl", "Formal Verification"],
            gaps=["No explicit UVM evidence"],
            hard_blocks=[],
            reasons=["Strong verified skill and domain alignment."],
            evidence=[{"type": "skill", "text": "Python"}],
        )
        session.add(match)

        resume = DocumentVersion(
            profile_id=profile.id,
            job_id=job.id,
            document_type="resume",
            version=1,
            status="approved",
            title="Jordan Taylor - Formal Verification Engineer",
            content={
                "summary": "Verification engineer specializing in Python and Tcl automation.",
                "skills": ["Python", "Tcl", "SystemVerilog", "Formal Verification"],
            },
            evidence=[{"type": "experience", "text": profile.experiences[0].description}],
            keyword_coverage={"matched": ["python", "tcl", "formal verification"], "missing": []},
        )
        session.add(resume)
        session.flush()

        run = AutomationRun(
            profile_id=profile.id,
            job_id=job.id,
            resume_id=resume.id,
            adapter="generic",
            application_url=job.application_url,
            status="dry_run_complete",
            dry_run=True,
            approved=True,
            checkpoint="stopped_before_submit",
            field_snapshot=[
                {
                    "label": "Email",
                    "value": DEMO_EMAIL,
                    "source": "verified profile",
                    "confidence": 1.0,
                    "sensitive": False,
                    "requires_review": False,
                },
                {
                    "label": "Will you require sponsorship?",
                    "value": "Review required",
                    "source": "user decision",
                    "confidence": 1.0,
                    "sensitive": True,
                    "requires_review": True,
                },
            ],
            validation_errors=[],
        )
        session.add(run)
        session.flush()
        session.add(
            Application(
                profile_id=profile.id,
                job_id=job.id,
                automation_run_id=run.id,
                status="ready",
                source="demo",
                tags=["demo", "dry-run"],
                metadata_json={"no_real_submission": True},
            )
        )
        session.commit()
        print(f"Demo seeded. Job ID: {job.id}")
        print("No real application was opened or submitted.")


if __name__ == "__main__":
    main()
