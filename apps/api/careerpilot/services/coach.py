import re
from datetime import UTC, datetime
from statistics import mean
from typing import Any
from uuid import UUID

from careerpilot.models import CareerProfile, Job
from careerpilot.models.coach import (
    CareerGoal,
    CareerRoadmap,
    InterviewQuestion,
    LearningPlan,
    MockInterviewResponse,
    MockInterviewSession,
    OfferComparison,
)
from careerpilot.repositories.coach import CoachRepository
from careerpilot.services.ai import AIProvider

QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "question": {"type": "string"},
                    "rationale": {"type": "string"},
                    "difficulty": {"type": "string"},
                },
                "required": ["category", "question", "rationale", "difficulty"],
            },
        }
    },
    "required": ["questions"],
}


class CoachService:
    def __init__(self, repository: CoachRepository, provider: AIProvider | None = None) -> None:
        self.repository = repository
        self.provider = provider

    @staticmethod
    def evidence(profile: CareerProfile) -> list[dict[str, str]]:
        values = [
            {"type": "skill", "id": str(item.id), "text": item.name}
            for item in profile.skills
        ]
        values.extend(
            {
                "type": "experience",
                "id": str(item.id),
                "text": f"{item.title} at {item.company}: {item.description or ''}".strip(),
            }
            for item in profile.experiences
        )
        values.extend(
            {
                "type": "project",
                "id": str(item.id),
                "text": f"{item.name}: {item.description or ''}".strip(),
            }
            for item in profile.projects
        )
        values.extend(
            {
                "type": "achievement",
                "id": str(item.id),
                "text": f"{item.title}: {item.description}",
            }
            for item in profile.achievements
        )
        return values

    def create_goal(self, profile_id: UUID, values: dict[str, Any]) -> CareerGoal:
        return self.repository.save(CareerGoal(profile_id=profile_id, **values))

    def generate_questions(
        self,
        profile: CareerProfile,
        job: Job | None,
        categories: list[str],
        count: int,
    ) -> list[InterviewQuestion]:
        evidence = self.evidence(profile)
        raw: list[dict[str, str]] = []
        if self.provider is not None:
            prompt = (
                "Generate interview questions using only the supplied verified candidate evidence "
                "and job context. Do not assert unverified candidate facts.\n"
                f"Categories: {categories}\nJob: {self._job_context(job)}\n"
                f"Verified evidence: {evidence}"
            )
            try:
                raw = list(self.provider.generate_json(prompt, QUESTION_SCHEMA)["questions"])
            except Exception:
                raw = []
        if not raw:
            raw = self._fallback_questions(job, categories)
        hints = evidence[:6]
        values = [
            InterviewQuestion(
                profile_id=profile.id,
                job_id=job.id if job else None,
                category=item["category"],
                question=item["question"],
                rationale=item["rationale"],
                difficulty=item.get("difficulty", "medium"),
                evidence_hints=hints,
            )
            for item in raw[:count]
        ]
        return self.repository.save_all(values)

    def create_session(
        self, profile_id: UUID, values: dict[str, Any], questions: list[InterviewQuestion]
    ) -> MockInterviewSession:
        question_ids = values.pop("question_ids")
        if not question_ids:
            question_ids = [str(item.id) for item in questions[:10]]
        else:
            question_ids = [str(item) for item in question_ids]
        return self.repository.save(
            MockInterviewSession(
                profile_id=profile_id, question_ids=question_ids, **values
            )
        )

    def answer(
        self,
        session: MockInterviewSession,
        question: InterviewQuestion,
        answer: str,
        profile: CareerProfile,
    ) -> MockInterviewResponse:
        lowered = answer.casefold()
        markers = {
            "situation": ("situation", "context", "when", "while"),
            "task": ("task", "goal", "responsible", "needed"),
            "action": ("action", "i implemented", "i created", "i led", "i analyzed"),
            "result": ("result", "outcome", "improved", "reduced", "increased", "%"),
        }
        star = {
            name: min(1.0, 0.35 * sum(marker in lowered for marker in candidates))
            for name, candidates in markers.items()
        }
        length_score = min(1.0, len(answer.split()) / 120)
        score = round(100 * (0.75 * mean(star.values()) + 0.25 * length_score), 1)
        evidence = [
            item for item in self.evidence(profile) if self._overlap(item["text"], answer)
        ][:5]
        strengths = [
            f"Clear {name} component" for name, value in star.items() if value >= 0.7
        ]
        improvements = [
            f"Make the {name} more explicit" for name, value in star.items() if value < 0.7
        ]
        if not evidence:
            improvements.append("Ground the answer in a verified experience or project.")
        response = self.repository.save(
            MockInterviewResponse(
                session_id=session.id,
                question_id=question.id,
                answer=answer,
                star_scores=star,
                strengths=strengths,
                improvements=improvements,
                evidence_used=evidence,
                score=score,
            )
        )
        session.current_index += 1
        if session.current_index >= len(session.question_ids):
            session.status = "completed"
            session.completed_at = datetime.now(UTC)
        responses = self.repository.responses(session.id)
        session.overall_score = round(mean(item.score for item in responses), 1)
        session.feedback = {
            "strengths": sorted({value for item in responses for value in item.strengths}),
            "improvements": sorted(
                {value for item in responses for value in item.improvements}
            ),
        }
        self.repository.save(session)
        return response

    def learning_plan(
        self, profile: CareerProfile, target_role: str, job: Job | None
    ) -> LearningPlan:
        known = {skill.name.casefold() for skill in profile.skills}
        target_text = f"{target_role} {job.description if job else ''}".casefold()
        catalog = (
            "python", "sql", "docker", "kubernetes", "aws", "azure", "leadership",
            "systemverilog", "uvm", "tcl", "formal verification",
        )
        gaps = [
            {"skill": skill.title(), "evidence": "Target role or job description"}
            for skill in catalog
            if skill in target_text and skill not in known
        ]
        recommendations = [
            {
                "skill": item["skill"],
                "action": f"Complete one practical {item['skill']} project and document evidence.",
                "priority": index + 1,
                "cost": "free/open-source resources",
            }
            for index, item in enumerate(gaps[:8])
        ]
        return self.repository.save(
            LearningPlan(
                profile_id=profile.id,
                title=f"Learning plan for {target_role}",
                target_role=target_role,
                gap_analysis=gaps,
                recommendations=recommendations,
            )
        )

    def roadmap(
        self, profile_id: UUID, title: str, horizon_months: int, goals: list[CareerGoal]
    ) -> CareerRoadmap:
        milestones = [
            {
                "month": max(1, round((index + 1) * horizon_months / max(1, len(goals)))),
                "goal_id": str(goal.id),
                "title": goal.title,
                "success_measure": goal.description or "Goal completed and evidence recorded.",
            }
            for index, goal in enumerate(goals)
        ]
        return self.repository.save(
            CareerRoadmap(
                profile_id=profile_id,
                title=title,
                horizon_months=horizon_months,
                milestones=milestones,
                assumptions=["Roadmap is guidance, not a guarantee of employment outcomes."],
            )
        )

    def compare_offers(
        self,
        profile_id: UUID,
        title: str,
        offers: list[dict[str, Any]],
        weights: dict[str, float],
    ) -> OfferComparison:
        effective = weights or {
            "base_salary": 0.35,
            "total_compensation": 0.25,
            "role_fit": 0.2,
            "location_fit": 0.1,
            "growth": 0.1,
        }
        scores: list[dict[str, Any]] = []
        numeric_fields = tuple(effective)
        maxima = {
            field: max(float(offer.get(field, 0) or 0) for offer in offers)
            for field in numeric_fields
        }
        for offer in offers:
            score = sum(
                (float(offer.get(field, 0) or 0) / maxima[field] if maxima[field] else 0)
                * weight
                for field, weight in effective.items()
            )
            scores.append({"name": offer.get("name", "Offer"), "score": round(score * 100, 1)})
        ranked = sorted(scores, key=lambda item: item["score"], reverse=True)
        return self.repository.save(
            OfferComparison(
                profile_id=profile_id,
                title=title,
                offers=offers,
                weights=effective,
                result={"ranking": ranked, "recommended": ranked[0]["name"]},
            )
        )

    @staticmethod
    def _fallback_questions(job: Job | None, categories: list[str]) -> list[dict[str, str]]:
        company = job.company.name if job and job.company else "this company"
        role = job.title if job else "your target role"
        templates = {
            "behavioral": [
                f"Tell me about a difficult problem you solved that is relevant to {role}.",
                "Describe a time you influenced a decision without formal authority.",
                "Tell me about a failure and what you changed afterward.",
            ],
            "technical": [
                f"Walk through how you would approach a core technical challenge in {role}.",
                "How do you validate the quality and reliability of your technical work?",
                "Explain a complex system you designed or improved.",
            ],
            "company": [
                f"Why are you interested in {company} and this role?",
                f"What would you aim to accomplish in your first 90 days at {company}?",
            ],
            "resume": [
                "Which achievement on your resume best demonstrates readiness for this role?",
                "Walk me through the most relevant project in your background.",
            ],
        }
        return [
            {
                "category": category,
                "question": question,
                "rationale": "Practice a concise answer grounded in verified career evidence.",
                "difficulty": "medium",
            }
            for category in categories
            for question in templates.get(category, [])
        ]

    @staticmethod
    def _job_context(job: Job | None) -> str:
        if job is None:
            return "No specific job selected."
        return f"{job.title} at {job.company.name}. {job.description}"

    @staticmethod
    def _overlap(evidence: str, answer: str) -> bool:
        tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", evidence.casefold()))
        answer_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", answer.casefold()))
        return len(tokens & answer_tokens) >= 2
