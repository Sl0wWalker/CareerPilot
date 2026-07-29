def test_innovation_lab_experiment_benchmark_and_promotion(client):
    experiment = client.post(
        "/api/v1/research/experiments",
        json={
            "slug": "multimodal-resume-analysis",
            "name": "Multimodal resume analysis",
            "hypothesis": "Layout-aware analysis improves extraction quality.",
            "category": "multimodal",
            "feature_flag": "research.multimodal_resume",
            "success_criteria": {"overall_quality": 0.85},
        },
    )
    assert experiment.status_code == 201
    experiment_id = experiment.json()["id"]

    dataset = client.post(
        "/api/v1/research/datasets",
        json={"name": "sanitized-resumes", "modality": "multimodal", "item_count": 25},
    )
    assert dataset.status_code == 201

    run = client.post(
        f"/api/v1/research/experiments/{experiment_id}/runs",
        json={
            "dataset_id": dataset.json()["id"],
            "model_provider": "ollama",
            "model_name": "qwen3:8b",
            "metrics": {"overall_quality": 0.91, "groundedness": 0.94},
            "safety_results": {
                "truthfulness": "pass",
                "privacy": "pass",
                "bias": "pass",
                "prompt_injection": "pass",
            },
            "latency_ms": 1234,
        },
    )
    assert run.status_code == 201
    assert run.json()["evaluation"]["safety_passed"] is True

    benchmarks = client.get("/api/v1/research/benchmarks")
    assert benchmarks.status_code == 200
    assert benchmarks.json()[0]["model"] == "qwen3:8b"

    feature = client.post(
        "/api/v1/research/incubator",
        json={
            "key": "incubator.multimodal_resume",
            "name": "Multimodal resume analysis",
            "experiment_id": experiment_id,
        },
    )
    promoted = client.post(
        f"/api/v1/research/incubator/{feature.json()['id']}/promote",
        json={"target_stage": "production", "rollout_percentage": 10},
    )
    assert promoted.status_code == 200
    assert promoted.json()["decision"]["eligible"] is True


def test_unsafe_experiment_cannot_be_promoted(client):
    experiment = client.post(
        "/api/v1/research/experiments",
        json={
            "slug": "voice-foundation",
            "name": "Voice foundation",
            "hypothesis": "Voice improves accessibility for guided workflows.",
            "category": "voice",
            "feature_flag": "research.voice",
            "success_criteria": {"overall_quality": 0.8},
        },
    ).json()
    feature = client.post(
        "/api/v1/research/incubator",
        json={
            "key": "incubator.voice",
            "name": "Voice foundation",
            "experiment_id": experiment["id"],
        },
    ).json()
    response = client.post(
        f"/api/v1/research/incubator/{feature['id']}/promote",
        json={"target_stage": "production", "rollout_percentage": 100},
    )
    assert response.status_code == 409
