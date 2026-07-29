import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Experiment = {
  id: string;
  name: string;
  category: string;
  status: string;
  enabled: boolean;
  hypothesis: string;
  feature_flag: string;
};

type Benchmark = {
  provider: string;
  model: string;
  runs: number;
  average_quality: number;
  average_latency_ms: number | null;
  safety_pass_rate: number;
};

export function ResearchWorkspace() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [experimentResponse, benchmarkResponse] = await Promise.all([
      apiFetch("/api/v1/research/experiments"),
      apiFetch("/api/v1/research/benchmarks"),
    ]);
    if (experimentResponse.ok) setExperiments(await experimentResponse.json());
    if (benchmarkResponse.ok) setBenchmarks(await benchmarkResponse.json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createStarterExperiment() {
    const response = await apiFetch("/api/v1/research/experiments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        slug: `agent-workflow-${Date.now()}`,
        name: "Supervised agent workflow",
        description:
          "Compare safe, resumable agent plans without affecting production.",
        hypothesis:
          "Checkpointed agents improve completion while preserving user control.",
        category: "agent-workflow",
        feature_flag: `research.agent_workflow_${Date.now()}`,
        success_criteria: { overall_quality: 0.85 },
      }),
    });
    setMessage(
      response.ok
        ? "Experiment created behind a disabled research flag."
        : "Unable to create experiment.",
    );
    if (response.ok) await load();
  }

  return (
    <section className="review" aria-labelledby="research-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">CAREERPILOT 2.0</p>
          <h1 id="research-title">Innovation Lab</h1>
          <p className="muted">
            Prototype, benchmark, and safety-test new AI capabilities before
            they can reach production.
          </p>
        </div>
        <button
          type="button"
          className="button"
          onClick={() => void createStarterExperiment()}
        >
          New agent experiment
        </button>
      </div>
      <p aria-live="polite">{message}</p>

      <div className="onboarding-grid">
        <article className="panel">
          <h2>Experiment Dashboard</h2>
          <strong className="metric-value">{experiments.length}</strong>
          <p className="muted">Tracked experiments</p>
          <ul>
            {experiments.slice(0, 5).map((experiment) => (
              <li key={experiment.id}>
                <strong>{experiment.name}</strong> · {experiment.category} ·{" "}
                {experiment.enabled ? "enabled" : "flagged off"}
              </li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <h2>Model Benchmarks</h2>
          {benchmarks.length === 0 ? (
            <p className="muted">Record an evaluated run to compare models.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Quality</th>
                  <th>Safety</th>
                </tr>
              </thead>
              <tbody>
                {benchmarks.map((benchmark) => (
                  <tr key={`${benchmark.provider}/${benchmark.model}`}>
                    <td>{benchmark.model}</td>
                    <td>{Math.round(benchmark.average_quality * 100)}%</td>
                    <td>{Math.round(benchmark.safety_pass_rate * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </article>

        <article className="panel">
          <h2>Feature Incubator</h2>
          <p className="muted">
            Ideas progress through prototype and validated stages. Production
            promotion is blocked until every recorded quality and safety gate
            passes.
          </p>
          <ul>
            <li>Multimodal resume and portfolio analysis</li>
            <li>Voice interaction foundations</li>
            <li>Agent workflow research</li>
            <li>Prompt and model evaluations</li>
          </ul>
        </article>
      </div>
    </section>
  );
}
