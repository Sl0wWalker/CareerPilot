import math
import re
from datetime import UTC, datetime
from typing import Any

from careerpilot.models import CareerProfile, Job, JobMatch, MatchingSettings
from careerpilot.repositories import MatchingRepository
from careerpilot.schemas.matching import DEFAULT_WEIGHTS
from careerpilot.services.ai import AIProvider

ENGINE_VERSION = "1.0"
TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}")
SENIORITY = ("intern", "junior", "entry", "mid", "senior", "staff", "principal", "lead")
DEGREES = ("bachelor", "master", "phd", "doctorate", "b.s.", "m.s.")


def words(value: str | None) -> set[str]:
    return {item.casefold() for item in TOKEN.findall(value or "")}


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    return sum(x * y for x, y in zip(left, right, strict=True)) / denominator if denominator else 0


class MatchingService:
    def __init__(
        self, repository: MatchingRepository, provider: AIProvider | None = None
    ) -> None:
        self.repository = repository
        self.provider = provider

    def analyze(
        self, job: Job, profile: CareerProfile, settings: MatchingSettings | None = None
    ) -> JobMatch:
        weights = (settings.weights if settings and settings.weights else DEFAULT_WEIGHTS).copy()
        description = job.description.casefold()
        job_words = words(f"{job.title} {job.description}")
        profile_skills = {skill.name.casefold(): skill for skill in profile.skills}
        matched_skills = sorted(name for name in profile_skills if name in description)
        required_candidates = self._required_skills(job.description, set(profile_skills))
        missing_skills = sorted(required_candidates - set(matched_skills))

        skill_score = (
            100 * len(matched_skills) / max(1, len(required_candidates))
            if required_candidates
            else min(100, len(matched_skills) * 20)
        )
        experience_text = " ".join(
            f"{item.title} {item.description or ''}" for item in profile.experiences
        )
        experience_overlap = job_words & words(experience_text)
        experience_score = min(100, 25 + len(experience_overlap) * 5) if profile.experiences else 0

        job_level = next((level for level in SENIORITY if level in job.title.casefold()), None)
        profile_levels = {
            level
            for item in profile.experiences
            for level in SENIORITY
            if level in item.title.casefold()
        }
        seniority_score = 100 if not job_level or job_level in profile_levels else 55

        education_required = next((degree for degree in DEGREES if degree in description), None)
        education_text = " ".join(
            f"{item.degree} {item.field_of_study or ''}" for item in profile.education
        )
        education_score = (
            100 if not education_required or education_required in education_text.casefold() else 25
        )

        preference = profile.job_preference
        preferred_locations = words(preference.preferred_locations if preference else None)
        job_location = words(job.location_raw)
        remote_match = bool(preference and preference.remote_ok and job.workplace_type == "remote")
        location_score = 100 if remote_match or not preferred_locations else (
            100 if preferred_locations & job_location else 35
        )

        sponsorship_prohibited = any(
            phrase in description
            for phrase in ("no sponsorship", "cannot sponsor", "without sponsorship")
        )
        needs_sponsorship = bool(preference and preference.requires_sponsorship)
        authorization_score = 0 if sponsorship_prohibited and needs_sponsorship else 100
        hard_blocks = (
            ["Job explicitly states sponsorship is unavailable."]
            if sponsorship_prohibited and needs_sponsorship
            else []
        )

        profile_words = words(
            " ".join(
                [skill.name for skill in profile.skills]
                + [item.title for item in profile.experiences]
                + [item.description or "" for item in profile.experiences]
                + [item.description or "" for item in profile.projects]
            )
        )
        meaningful_job_words = {
            item
            for item in job_words
            if len(item) > 3 and item not in {"with", "from", "this", "that"}
        }
        keyword_matches = sorted(profile_words & meaningful_job_words)
        keyword_score = min(
            100,
            100 * len(keyword_matches) / max(1, min(20, len(meaningful_job_words))),
        )

        semantic_score, semantic_confidence = self._semantic_score(job, profile)
        raw = {
            "skills": (skill_score, 0.9, matched_skills, missing_skills),
            "experience": (experience_score, 0.75, sorted(experience_overlap)[:10], []),
            "seniority": (seniority_score, 0.7 if job_level else 0.4, list(profile_levels), []),
            "education": (education_score, 0.8 if education_required else 0.45, [], []),
            "location": (location_score, 0.85, sorted(preferred_locations & job_location), []),
            "work_authorization": (
                authorization_score,
                0.95 if sponsorship_prohibited else 0.45,
                [],
                hard_blocks,
            ),
            "keywords": (keyword_score, 0.7, keyword_matches[:12], []),
            "semantic_similarity": (semantic_score, semantic_confidence, [], []),
        }
        components: dict[str, dict[str, Any]] = {}
        for name, (score, confidence, matched, missing) in raw.items():
            components[name] = {
                "score": round(score, 1),
                "weight": weights[name],
                "weighted_score": round(score * weights[name], 1),
                "confidence": confidence,
                "explanation": self._explanation(name, score),
                "matched": matched,
                "missing": missing,
            }
        overall = round(sum(item["weighted_score"] for item in components.values()), 1)
        confidence = round(
            sum(item["confidence"] * item["weight"] for item in components.values()), 2
        )
        threshold = settings.minimum_recommendation_score if settings else 65
        recommendation = (
            "blocked"
            if hard_blocks
            else "strong_match"
            if overall >= max(80, threshold)
            else "consider"
            if overall >= threshold
            else "low_match"
        )
        strengths = [f"Matched skill: {item}" for item in matched_skills[:8]]
        gaps = [f"Missing or unverified skill: {item}" for item in missing_skills[:8]]
        reasons = self._reasons(overall, recommendation, components)
        evidence = [
            {"type": "skill", "id": str(profile_skills[name].id), "text": name}
            for name in matched_skills
        ]

        match = self.repository.match(job.id, profile.id)
        values = {
            "overall_score": overall,
            "confidence": confidence,
            "recommendation": recommendation,
            "engine_version": ENGINE_VERSION,
            "components": components,
            "strengths": strengths,
            "gaps": gaps,
            "hard_blocks": hard_blocks,
            "reasons": reasons,
            "evidence": evidence,
        }
        if match is None:
            match = JobMatch(job_id=job.id, profile_id=profile.id, **values)
        else:
            for key, value in values.items():
                setattr(match, key, value)
            match.updated_at = datetime.now(UTC)
        return self.repository.save_match(match)

    def _required_skills(self, description: str, known: set[str]) -> set[str]:
        lowered = description.casefold()
        detected = {name for name in known if name in lowered}
        common = {
            "python", "java", "javascript", "typescript", "sql", "aws", "azure", "docker",
            "kubernetes", "linux", "tcl", "perl", "systemverilog", "uvm", "formality",
            "conformal", "git", "react", "fastapi",
        }
        return detected | {name for name in common if re.search(rf"\b{re.escape(name)}\b", lowered)}

    def _semantic_score(self, job: Job, profile: CareerProfile) -> tuple[float, float]:
        if self.provider is None:
            return 50, 0.2
        profile_text = " ".join(
            [skill.name for skill in profile.skills]
            + [f"{item.title} {item.description or ''}" for item in profile.experiences]
            + [item.description or item.name for item in profile.projects]
        )
        try:
            job_vector, profile_vector = self.provider.embed([job.description, profile_text])
            return round(max(0, cosine(job_vector, profile_vector)) * 100, 1), 0.85
        except Exception:
            return 50, 0.2

    @staticmethod
    def _explanation(name: str, score: float) -> str:
        label = name.replace("_", " ")
        strength = "strong" if score >= 75 else "partial" if score >= 45 else "weak"
        return f"{label.title()} alignment is {strength}."

    @staticmethod
    def _reasons(
        overall: float, recommendation: str, components: dict[str, dict[str, Any]]
    ) -> list[str]:
        ranked = sorted(
            components.items(), key=lambda item: item[1]["weighted_score"], reverse=True
        )
        return [
            f"Overall evidence-backed score is {overall:.1f}%.",
            f"Recommendation: {recommendation.replace('_', ' ')}.",
            f"Highest contribution: {ranked[0][0].replace('_', ' ')}.",
        ]
