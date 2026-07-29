import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Overview = {
  strategies: number;
  active_monitors: number;
  configured_agents: number;
  enabled_agents: number;
  approval_required_agents: number;
  rising_skills: Array<{
    skill: string;
    current_demand: number;
    projected_demand: number;
    confidence: number;
  }>;
  market_insights: Array<{
    id: string;
    type: string;
    title: string;
    summary: string;
    confidence: number;
  }>;
  recruiter_engagement: {
    known_contacts: number;
    applications: number;
    contact_coverage: number;
  };
  opportunity_pipeline: Record<string, number>;
};

type Strategy = {
  id: string;
  title: string;
  horizon_months: number;
  target_roles: string[];
  status: string;
};

type Monitor = {
  id: string;
  name: string;
  cadence: string;
  enabled: boolean;
  last_result: Record<string, unknown>;
};

type Agent = {
  id: string;
  agent_key: string;
  display_name: string;
  objective: string;
  enabled: boolean;
  autonomy_level: string;
};

export function IntelligenceWorkspace() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tab, setTab] = useState<"hub" | "strategy" | "monitor" | "agents">(
    "hub",
  );
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const responses = await Promise.all([
      apiFetch("/api/v1/intelligence/overview"),
      apiFetch("/api/v1/intelligence/strategies"),
      apiFetch("/api/v1/intelligence/monitors"),
      apiFetch("/api/v1/intelligence/agents"),
    ]);
    if (responses[0].ok) setOverview(await responses[0].json());
    if (responses[1].ok) setStrategies(await responses[1].json());
    if (responses[2].ok) setMonitors(await responses[2].json());
    if (responses[3].ok) setAgents(await responses[3].json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createStrategy() {
    const response = await apiFetch("/api/v1/intelligence/strategies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: "Next role strategy",
        horizon_months: 12,
        target_roles: ["Senior Engineer"],
        objectives: [
          { milestone: "Build target-role evidence", target_month: 3 },
        ],
        constraints: { preserve_truthful_profile: true },
      }),
    });
    setMessage(
      response.ok ? "Career strategy created." : "Could not create strategy.",
    );
    await load();
  }

  async function createMonitor() {
    const response = await apiFetch("/api/v1/intelligence/monitors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "High-fit opportunity watch",
        cadence: "daily",
        criteria: { minimum_match: 80, sponsorship_compatible: true },
      }),
    });
    setMessage(
      response.ok
        ? "Opportunity monitor enabled."
        : "Could not create monitor.",
    );
    await load();
  }

  async function configureAgent() {
    const response = await apiFetch(
      "/api/v1/intelligence/agents/opportunity-scout",
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_key: "opportunity-scout",
          display_name: "Opportunity Scout",
          objective: "Monitor high-fit jobs and prepare recommendations",
          enabled: true,
          autonomy_level: "prepare",
          approval_policy: {
            external_writes: "always",
            applications: "always",
            messages: "always",
          },
          capabilities: [
            "jobs.search",
            "matching.analyze",
            "notifications.create",
          ],
          schedule: { cadence: "daily" },
        }),
      },
    );
    setMessage(
      response.ok
        ? "Agent configured with approval boundaries."
        : "Could not configure agent.",
    );
    await load();
  }

  return (
    <section className="review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">CAREER INTELLIGENCE HUB</p>
          <h1>Turn career signals into supervised action.</h1>
          <p className="muted">
            Monitor opportunities, forecast skill demand, and coordinate agents
            while every external action remains approval-gated.
          </p>
        </div>
        <span className="status status-online">
          <span className="status-dot" /> Human control active
        </span>
      </div>

      <nav className="view-tabs" aria-label="Intelligence workspace">
        {(["hub", "strategy", "monitor", "agents"] as const).map((item) => (
          <button
            type="button"
            className={tab === item ? "active" : ""}
            onClick={() => setTab(item)}
            key={item}
          >
            {item === "hub"
              ? "Intelligence hub"
              : item === "strategy"
                ? "Strategy planner"
                : item === "monitor"
                  ? "Opportunity monitor"
                  : "Agent dashboard"}
          </button>
        ))}
      </nav>

      {message && <p className="panel">{message}</p>}

      {tab === "hub" && (
        <>
          <div className="onboarding-grid">
            <article className="panel">
              <strong>{overview?.active_monitors ?? 0}</strong>
              <h2>Active monitors</h2>
              <p className="muted">
                Continuously watching configured criteria.
              </p>
            </article>
            <article className="panel">
              <strong>{overview?.enabled_agents ?? 0}</strong>
              <h2>Enabled agents</h2>
              <p className="muted">
                {overview?.approval_required_agents ?? 0} require approval.
              </p>
            </article>
            <article className="panel">
              <strong>
                {Math.round(
                  (overview?.recruiter_engagement.contact_coverage ?? 0) * 100,
                )}
                %
              </strong>
              <h2>Recruiter coverage</h2>
              <p className="muted">Contacts linked to applications.</p>
            </article>
          </div>
          <div className="workspace">
            <article className="panel">
              <p className="eyebrow">SKILL TREND FORECAST</p>
              <h2>Rising capabilities</h2>
              {overview?.rising_skills.length ? (
                overview.rising_skills.map((skill) => (
                  <div className="history-row" key={skill.skill}>
                    <strong>{skill.skill}</strong>
                    <span>
                      {Math.round(skill.current_demand * 100)}% →{" "}
                      {Math.round(skill.projected_demand * 100)}%
                    </span>
                    <em>{Math.round(skill.confidence * 100)}% confidence</em>
                  </div>
                ))
              ) : (
                <p className="empty">
                  Forecasts appear as verified market evidence accumulates.
                </p>
              )}
            </article>
            <article className="panel">
              <p className="eyebrow">MARKET INSIGHTS</p>
              <h2>Evidence-backed signals</h2>
              {overview?.market_insights.length ? (
                overview.market_insights.map((insight) => (
                  <div className="history-row" key={insight.id}>
                    <strong>{insight.title}</strong>
                    <span>{insight.summary}</span>
                    <em>{insight.type}</em>
                  </div>
                ))
              ) : (
                <p className="empty">
                  No market insights have been generated yet.
                </p>
              )}
            </article>
          </div>
        </>
      )}

      {tab === "strategy" && (
        <article className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STRATEGY PLANNER</p>
              <h2>Long-term career plans</h2>
            </div>
            <button type="button" onClick={() => void createStrategy()}>
              Create strategy
            </button>
          </div>
          {strategies.map((strategy) => (
            <div className="history-row" key={strategy.id}>
              <strong>{strategy.title}</strong>
              <span>{strategy.target_roles.join(", ")}</span>
              <em>{strategy.horizon_months} months</em>
            </div>
          ))}
          {!strategies.length && <p className="empty">No strategies yet.</p>}
        </article>
      )}

      {tab === "monitor" && (
        <article className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">OPPORTUNITY MONITOR</p>
              <h2>Proactive discovery rules</h2>
            </div>
            <button type="button" onClick={() => void createMonitor()}>
              Add monitor
            </button>
          </div>
          {monitors.map((monitor) => (
            <div className="history-row" key={monitor.id}>
              <strong>{monitor.name}</strong>
              <span>{monitor.cadence}</span>
              <em>{monitor.enabled ? "Active" : "Paused"}</em>
            </div>
          ))}
          {!monitors.length && (
            <p className="empty">No opportunity monitors yet.</p>
          )}
        </article>
      )}

      {tab === "agents" && (
        <article className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">AGENT DASHBOARD</p>
              <h2>Coordinated, governed agents</h2>
            </div>
            <button type="button" onClick={() => void configureAgent()}>
              Configure scout
            </button>
          </div>
          {agents.map((agent) => (
            <div className="history-row" key={agent.id}>
              <strong>{agent.display_name}</strong>
              <span>{agent.objective}</span>
              <em>
                {agent.autonomy_level} ·{" "}
                {agent.enabled ? "Enabled" : "Disabled"}
              </em>
            </div>
          ))}
          {!agents.length && (
            <p className="empty">No autonomous agents configured.</p>
          )}
          <p className="muted">
            Agents reuse installed marketplace workflows and existing platform
            capabilities. Applications, messages, and other external writes
            always require explicit approval.
          </p>
        </article>
      )}
    </section>
  );
}
