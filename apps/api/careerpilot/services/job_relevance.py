import json

from careerpilot.models import Job
from careerpilot.repositories import CareerProfileRepository, JobRepository
from careerpilot.services.ai import AIProvider

RELEVANCE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
    "required": ["score", "strengths", "gaps", "reason"],
}


class JobRelevanceService:
    def __init__(
        self, jobs: JobRepository, profiles: CareerProfileRepository, provider: AIProvider
    ) -> None:
        self.jobs = jobs
        self.profiles = profiles
        self.provider = provider

    def analyze(self, job: Job) -> Job:
        profile = self.profiles.get_required()
        context = {
            "candidate": {
                "skills": [skill.name for skill in profile.skills],
                "experience": [
                    {"title": item.title, "company": item.company, "description": item.description}
                    for item in profile.experiences
                ],
            },
            "job": {
                "title": job.title,
                "company": job.company.name,
                "location": job.location_raw,
                "description": job.description,
            },
        }
        result = self.provider.generate_json(
            "Analyze relevance using only supplied evidence. Return JSON.\n"
            + json.dumps(context, indent=2),
            RELEVANCE_SCHEMA,
        )
        job.relevance_score = max(0.0, min(100.0, float(result["score"])))
        job.relevance_analysis = {
            "strengths": [str(item) for item in result["strengths"]],
            "gaps": [str(item) for item in result["gaps"]],
            "reason": str(result["reason"]),
            "method": "ai_assisted",
        }
        return self.jobs.save_job(job)

