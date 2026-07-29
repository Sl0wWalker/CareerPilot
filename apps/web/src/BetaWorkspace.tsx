import { type FormEvent, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Settings = {
  enrolled: boolean;
  diagnostics_opt_in: boolean;
  analytics_opt_in: boolean;
  release_channel: "stable" | "beta";
  onboarding_completed: boolean;
};

type Feedback = {
  id: string;
  kind: string;
  title: string;
  severity: string;
  status: string;
  created_at: string;
};

type Health = {
  feedback_total: number;
  open_bugs: number;
  feature_requests: number;
  satisfaction_average: number | null;
  opted_in_users: number;
  usage_events: number;
};

const defaultSettings: Settings = {
  enrolled: false,
  diagnostics_opt_in: false,
  analytics_opt_in: false,
  release_channel: "stable",
  onboarding_completed: false,
};

export function BetaWorkspace() {
  const [settings, setSettings] = useState(defaultSettings);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    void Promise.all([
      apiFetch("/api/v1/beta/settings").then((response) => response.json()),
      apiFetch("/api/v1/beta/feedback").then((response) => response.json()),
      apiFetch("/api/v1/beta/admin/health").then(async (response) =>
        response.ok ? response.json() : null,
      ),
    ]).then(([nextSettings, nextFeedback, nextHealth]) => {
      setSettings(nextSettings);
      setFeedback(nextFeedback);
      setHealth(nextHealth);
    });
  }, []);

  async function saveSettings(change: Partial<Settings>) {
    const response = await apiFetch("/api/v1/beta/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(change),
    });
    if (response.ok) setSettings(await response.json());
  }

  async function submitFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/beta/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: data.get("kind"),
        title: data.get("title"),
        description: data.get("description"),
        severity: data.get("severity"),
        page_url: window.location.href,
        diagnostics: {
          userAgent: navigator.userAgent,
          language: navigator.language,
        },
      }),
    });
    if (response.ok) {
      const item = await response.json();
      setFeedback((items) => [item, ...items]);
      setMessage("Thanks — your feedback was saved.");
      event.currentTarget.reset();
    }
  }

  return (
    <section className="beta-workspace">
      <div className="hero compact-hero">
        <p className="eyebrow">BETA PROGRAM</p>
        <h1>Help shape the next CareerPilot release.</h1>
        <p className="lede">
          Share feedback locally, choose your release channel, and opt in to
          anonymous product diagnostics only when you want to.
        </p>
      </div>

      <div className="beta-grid">
        <article className="panel">
          <p className="eyebrow">BETA SETTINGS</p>
          <Toggle
            label="Join the internal beta"
            checked={settings.enrolled}
            onChange={(value) => void saveSettings({ enrolled: value })}
          />
          <Toggle
            label="Share anonymous usage events"
            checked={settings.analytics_opt_in}
            onChange={(value) => void saveSettings({ analytics_opt_in: value })}
          />
          <Toggle
            label="Attach diagnostics to bug reports"
            checked={settings.diagnostics_opt_in}
            onChange={(value) =>
              void saveSettings({ diagnostics_opt_in: value })
            }
          />
          <label className="beta-field">
            Release channel
            <select
              value={settings.release_channel}
              onChange={(event) =>
                void saveSettings({
                  release_channel: event.target.value as "stable" | "beta",
                })
              }
            >
              <option value="stable">Stable</option>
              <option value="beta">Beta</option>
            </select>
          </label>
        </article>

        <form className="panel beta-form" onSubmit={submitFeedback}>
          <p className="eyebrow">FEEDBACK CENTER</p>
          <select name="kind" aria-label="Feedback type">
            <option value="feedback">General feedback</option>
            <option value="bug">Bug report</option>
            <option value="feature">Feature request</option>
          </select>
          <input
            name="title"
            minLength={3}
            placeholder="Short title"
            required
          />
          <textarea
            name="description"
            minLength={3}
            placeholder="What happened, or what would make CareerPilot better?"
            required
          />
          <select name="severity" aria-label="Severity">
            <option value="normal">Normal</option>
            <option value="low">Low</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <button className="button" type="submit">
            Send feedback
          </button>
          {message && <p className="good">{message}</p>}
        </form>
      </div>

      {health && (
        <section className="panel">
          <p className="eyebrow">ADMIN PRODUCT HEALTH</p>
          <div className="metric-grid">
            <Metric label="Feedback" value={health.feedback_total} />
            <Metric label="Open bugs" value={health.open_bugs} />
            <Metric label="Requests" value={health.feature_requests} />
            <Metric
              label="Satisfaction"
              value={health.satisfaction_average ?? "—"}
            />
            <Metric label="Opted in" value={health.opted_in_users} />
            <Metric label="Usage events" value={health.usage_events} />
          </div>
        </section>
      )}

      <section className="panel">
        <p className="eyebrow">YOUR REPORTS</p>
        {feedback.length === 0 ? (
          <p className="muted">No feedback submitted yet.</p>
        ) : (
          feedback.map((item) => (
            <div className="feedback-row" key={item.id}>
              <div>
                <strong>{item.title}</strong>
                <span>
                  {item.kind} · {item.severity}
                </span>
              </div>
              <em>{item.status}</em>
            </div>
          ))
        )}
      </section>
    </section>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="beta-toggle">
      <span>{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
