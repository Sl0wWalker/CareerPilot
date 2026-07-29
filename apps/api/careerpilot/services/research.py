from collections.abc import Iterable
from statistics import mean
from typing import Any

REQUIRED_SAFETY_CHECKS = ("truthfulness", "privacy", "bias", "prompt_injection")


def evaluate_run(
    metrics: dict[str, Any], safety_results: dict[str, Any], success_criteria: dict[str, Any]
) -> dict[str, Any]:
    numeric_metrics = {
        key: float(value)
        for key, value in metrics.items()
        if isinstance(value, int | float) and not isinstance(value, bool)
    }
    criteria = {
        key: float(value)
        for key, value in success_criteria.items()
        if isinstance(value, int | float) and not isinstance(value, bool)
    }
    metric_checks = {
        key: numeric_metrics.get(key, float("-inf")) >= threshold
        for key, threshold in criteria.items()
    }
    safety_checks = {
        key: safety_results.get(key) in (True, "pass", "passed") for key in REQUIRED_SAFETY_CHECKS
    }
    return {
        "quality_score": round(mean(numeric_metrics.values()), 4) if numeric_metrics else 0.0,
        "criteria_passed": all(metric_checks.values()) if metric_checks else False,
        "metric_checks": metric_checks,
        "safety_passed": all(safety_checks.values()),
        "safety_checks": safety_checks,
    }


def benchmark_summary(runs: Iterable[Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Any]] = {}
    for run in runs:
        grouped.setdefault((run.model_provider, run.model_name), []).append(run)
    result = []
    for (provider, model), model_runs in grouped.items():
        scores = [
            float(run.metrics.get("overall_quality", 0.0))
            for run in model_runs
            if isinstance(run.metrics, dict)
        ]
        latencies = [run.latency_ms for run in model_runs if run.latency_ms is not None]
        safe = sum(
            1
            for run in model_runs
            if all(run.safety_results.get(check) in (True, "pass", "passed")
                   for check in REQUIRED_SAFETY_CHECKS)
        )
        result.append(
            {
                "provider": provider,
                "model": model,
                "runs": len(model_runs),
                "average_quality": round(mean(scores), 4) if scores else 0.0,
                "average_latency_ms": round(mean(latencies), 2) if latencies else None,
                "safety_pass_rate": round(safe / len(model_runs), 4),
            }
        )
    return sorted(result, key=lambda item: item["average_quality"], reverse=True)


def promotion_decision(run_evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = bool(run_evaluations) and all(
        evaluation["criteria_passed"] and evaluation["safety_passed"]
        for evaluation in run_evaluations
    )
    return {
        "eligible": eligible,
        "reason": (
            "all recorded runs meet quality and safety gates"
            if eligible
            else "quality or safety evidence is incomplete"
        ),
    }
