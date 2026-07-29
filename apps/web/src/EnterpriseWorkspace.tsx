import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Organization = {
  id: string;
  name: string;
  slug: string;
  plan: string;
  enabled: boolean;
};

type Overview = {
  organizations: number;
  workspaces: number;
  members: number;
  active_agents: number;
  audit_events: number;
  quota_utilization: Record<string, number>;
  queue_backend: string;
  tenancy_mode: string;
};

type AgentRun = {
  id: string;
  agent_type: string;
  objective: string;
  status: string;
  created_at: string;
};

export function EnterpriseWorkspace() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [agents, setAgents] = useState<AgentRun[]>([]);
  const [selected, setSelected] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [overviewResponse, organizationsResponse] = await Promise.all([
      apiFetch("/api/v1/enterprise/overview"),
      apiFetch("/api/v1/enterprise/organizations"),
    ]);
    if (overviewResponse.ok) setOverview(await overviewResponse.json());
    if (organizationsResponse.ok) {
      const items: Organization[] = await organizationsResponse.json();
      setOrganizations(items);
      setSelected((value) => value || items[0]?.id || "");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!selected) return;
    void apiFetch(`/api/v1/enterprise/organizations/${selected}/agents`).then(
      async (response) => {
        if (response.ok) setAgents(await response.json());
      },
    );
  }, [selected]);

  async function createOrganization() {
    const suffix = organizations.length + 1;
    const response = await apiFetch("/api/v1/enterprise/organizations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: `CareerPilot Organization ${suffix}`,
        slug: `careerpilot-org-${suffix}`,
      }),
    });
    setMessage(
      response.ok
        ? "Organization created with an owner membership."
        : "Could not create organization.",
    );
    await load();
  }

  async function queueAgent() {
    if (!selected) return;
    const response = await apiFetch(
      `/api/v1/enterprise/organizations/${selected}/agents`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_type: "application-orchestrator",
          objective: "Prepare a supervised application workflow",
          input: { require_human_review: true },
        }),
      },
    );
    setMessage(
      response.ok
        ? "Agent workflow queued."
        : "Agent workflow could not be queued. Check quota and policy settings.",
    );
    if (response.ok) setAgents([await response.json(), ...agents]);
    await load();
  }

  return (
    <section className="review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ENTERPRISE CONTROL PLANE</p>
          <h1>Organizations, policy, and agents</h1>
          <p className="muted">
            Isolate workspaces, govern automation, and observe coordinated AI
            workflows.
          </p>
        </div>
        <button
          type="button"
          className="button"
          onClick={() => void createOrganization()}
        >
          Create organization
        </button>
      </div>

      <div className="onboarding-grid">
        <article className="panel">
          <strong>{overview?.organizations ?? 0}</strong>
          <h2>Organizations</h2>
          <p className="muted">{overview?.tenancy_mode ?? "Loading tenancy"}</p>
        </article>
        <article className="panel">
          <strong>{overview?.members ?? 0}</strong>
          <h2>Members</h2>
          <p className="muted">Role and permission assignments.</p>
        </article>
        <article className="panel">
          <strong>{overview?.active_agents ?? 0}</strong>
          <h2>Active agents</h2>
          <p className="muted">{overview?.queue_backend ?? "Loading queue"}</p>
        </article>
      </div>

      {message && <p className="panel">{message}</p>}

      <div className="workspace">
        <article className="panel">
          <p className="eyebrow">ORGANIZATION MANAGEMENT</p>
          <h2>Tenant directory</h2>
          {organizations.length === 0 ? (
            <p className="empty">Create an organization to begin.</p>
          ) : (
            organizations.map((organization) => (
              <button
                type="button"
                className="history-row"
                key={organization.id}
                onClick={() => setSelected(organization.id)}
              >
                <strong>{organization.name}</strong>
                <span>
                  {organization.plan} · {organization.slug}
                </span>
                <em>{organization.enabled ? "Active" : "Disabled"}</em>
              </button>
            ))
          )}
        </article>

        <article className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">AGENT CONSOLE</p>
              <h2>Coordinated workflows</h2>
            </div>
            <button
              type="button"
              disabled={!selected}
              onClick={() => void queueAgent()}
            >
              Queue agent
            </button>
          </div>
          {agents.length === 0 ? (
            <p className="empty">No agent runs for this organization.</p>
          ) : (
            agents.map((agent) => (
              <div className="history-row" key={agent.id}>
                <strong>{agent.agent_type}</strong>
                <span>{agent.objective}</span>
                <em>{agent.status}</em>
              </div>
            ))
          )}
        </article>
      </div>

      <div className="workspace">
        <article className="panel">
          <p className="eyebrow">ENTERPRISE SETTINGS</p>
          <h2>Identity and policy</h2>
          <p className="muted">
            OIDC/SAML foundations, advanced RBAC, human-review policy, immutable
            audit events, and tenant-scoped plugin configuration are available
            through the enterprise API.
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">USAGE & BILLING</p>
          <h2>Quota health</h2>
          {Object.entries(overview?.quota_utilization ?? {}).map(
            ([metric, utilization]) => (
              <p key={metric}>
                <strong>{metric}</strong> {Math.round(utilization * 100)}%
                utilized
              </p>
            ),
          )}
          {Object.keys(overview?.quota_utilization ?? {}).length === 0 && (
            <p className="empty">No quotas configured.</p>
          )}
        </article>
      </div>
    </section>
  );
}
