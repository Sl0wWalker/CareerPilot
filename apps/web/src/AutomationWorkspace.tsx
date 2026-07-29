import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type Run = {
  id: string;
  adapter: string;
  application_url: string;
  status: string;
  dry_run: boolean;
  approved: boolean;
  checkpoint: string;
  validation_errors: string[];
  field_snapshot: Array<{
    label: string;
    value: string | null;
    source: string;
    confidence: number;
    sensitive: boolean;
    requires_review: boolean;
  }>;
};

type Adapter = {
  adapter: string;
  enabled: boolean;
  headless: boolean;
  default_dry_run: boolean;
  timeout_ms: number;
};

export function AutomationWorkspace() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [adapters, setAdapters] = useState<Adapter[]>([]);
  const [selected, setSelected] = useState<Run | null>(null);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [runResponse, adapterResponse] = await Promise.all([
      fetch(`${API}/automation/runs`),
      fetch(`${API}/automation/adapters`),
    ]);
    if (runResponse.ok) setRuns(await runResponse.json());
    if (adapterResponse.ok) setAdapters(await adapterResponse.json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function action(name: "approve" | "execute") {
    if (!selected) return;
    const response = await fetch(
      `${API}/automation/runs/${selected.id}/${name}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body:
          name === "approve" ? JSON.stringify({ approved: true }) : undefined,
      },
    );
    const body = await response.json();
    if (!response.ok) {
      setMessage(body.detail ?? "Action failed.");
      return;
    }
    setSelected(body);
    setMessage(
      name === "approve"
        ? "Application package approved."
        : "Dry run completed at final review.",
    );
    await load();
  }

  async function toggle(adapter: Adapter) {
    const response = await fetch(
      `${API}/automation/adapters/${adapter.adapter}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !adapter.enabled }),
      },
    );
    if (response.ok) await load();
  }

  return (
    <section className="review automation-workspace">
      <div className="section-heading">
        <div>
          <p className="eyebrow">INTELLIGENT APPLICATION AUTOMATION</p>
          <h1>Fill safely. Review everything. Submit deliberately.</h1>
        </div>
      </div>
      <div className="automation-grid">
        <article className="panel">
          <h2>Automation queue</h2>
          {runs.length === 0 ? (
            <p className="muted">No prepared applications yet.</p>
          ) : (
            runs.map((run) => (
              <button
                type="button"
                className="history-row"
                key={run.id}
                onClick={() => setSelected(run)}
              >
                <strong>{run.adapter}</strong>
                <span>{run.application_url}</span>
                <em>{run.status.replaceAll("_", " ")}</em>
              </button>
            ))
          )}
        </article>
        <article className="panel">
          <h2>Adapter settings</h2>
          {adapters.map((adapter) => (
            <div className="adapter-row" key={adapter.adapter}>
              <div>
                <strong>{adapter.adapter}</strong>
                <p>Visible browser · {adapter.timeout_ms / 1000}s timeout</p>
              </div>
              <button type="button" onClick={() => void toggle(adapter)}>
                {adapter.enabled ? "Enabled" : "Disabled"}
              </button>
            </div>
          ))}
        </article>
      </div>
      {selected && (
        <article className="panel application-review">
          <div className="section-heading">
            <div>
              <p className="eyebrow">APPLICATION REVIEW</p>
              <h2>
                {selected.adapter} · {selected.status.replaceAll("_", " ")}
              </h2>
              <p className="muted">Checkpoint: {selected.checkpoint}</p>
            </div>
            <div className="fact-actions">
              <button
                type="button"
                className="accept"
                disabled={selected.validation_errors.length > 0}
                onClick={() => void action("approve")}
              >
                Approve package
              </button>
              <button
                type="button"
                disabled={!selected.approved}
                onClick={() => void action("execute")}
              >
                Run dry fill
              </button>
            </div>
          </div>
          {selected.validation_errors.map((error) => (
            <p className="warning-text" key={error}>
              ⚠ {error}
            </p>
          ))}
          <div className="mapped-fields">
            {selected.field_snapshot.map((field) => (
              <div
                key={field.label}
                className={field.requires_review ? "needs-review" : ""}
              >
                <strong>{field.label}</strong>
                <span>{field.value ?? "Needs input"}</span>
                <small>
                  {field.source} · {Math.round(field.confidence * 100)}%
                </small>
              </div>
            ))}
          </div>
          <p aria-live="polite">{message}</p>
        </article>
      )}
    </section>
  );
}
