import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Package = {
  id: string;
  name: string;
  summary: string;
  package_type: string;
  version: string;
  rating: number;
};
type Installation = {
  id: string;
  package_slug: string;
  installed_version: string;
  enabled: boolean;
};
type Workflow = { id: string; name: string; version: number };

export function MarketplaceWorkspace() {
  const [tab, setTab] = useState<
    "marketplace" | "studio" | "packages" | "publisher"
  >("marketplace");
  const [packages, setPackages] = useState<Package[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [a, b, c] = await Promise.all([
      apiFetch("/api/v1/marketplace/packages"),
      apiFetch("/api/v1/marketplace/installations"),
      apiFetch("/api/v1/marketplace/workflows"),
    ]);
    if (a.ok) setPackages(await a.json());
    if (b.ok) setInstallations(await b.json());
    if (c.ok) setWorkflows(await c.json());
  }, []);
  useEffect(() => {
    void load();
  }, [load]);

  async function install(item: Package) {
    const response = await apiFetch(
      `/api/v1/marketplace/packages/${item.id}/install`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: "stable", configuration: {} }),
      },
    );
    setMessage(
      response.ok ? `${item.name} installed.` : "Installation failed.",
    );
    await load();
  }

  async function createWorkflow() {
    const response = await apiFetch("/api/v1/marketplace/workflows", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Tailor, review, and apply",
        description: "Supervised application preparation.",
        trigger_type: "manual",
        graph: {
          nodes: [
            {
              id: "tailor",
              type: "ai",
              config: { prompt: "Tailor from verified facts" },
            },
            {
              id: "review",
              type: "approval",
              config: { message: "Review every claim" },
            },
            {
              id: "prepare",
              type: "action",
              config: { action: "application.prepare" },
            },
          ],
          edges: [
            { source: "tailor", target: "review" },
            { source: "review", target: "prepare" },
          ],
        },
      }),
    });
    setMessage(response.ok ? "Workflow saved." : "Workflow validation failed.");
    await load();
  }

  return (
    <section className="marketplace-workspace">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ECOSYSTEM</p>
          <h1>Marketplace & Automation Studio</h1>
          <p className="muted">
            Install signed extensions and compose approval-aware workflows.
          </p>
        </div>
      </div>
      <nav className="view-tabs" aria-label="Marketplace views">
        {(["marketplace", "studio", "packages", "publisher"] as const).map(
          (item) => (
            <button
              type="button"
              className={tab === item ? "active" : ""}
              onClick={() => setTab(item)}
              key={item}
            >
              {item === "studio" ? "Automation Studio" : item}
            </button>
          ),
        )}
      </nav>
      {message && <p className="good">{message}</p>}
      {tab === "marketplace" && (
        <div className="marketplace-grid">
          {packages.map((item) => (
            <article className="panel package-card" key={item.id}>
              <span className="source-pill">
                {item.package_type.replace("_", " ")}
              </span>
              <h2>{item.name}</h2>
              <p className="muted">{item.summary}</p>
              <small>
                v{item.version} · ★ {item.rating.toFixed(1)}
              </small>
              <button
                className="button"
                type="button"
                onClick={() => void install(item)}
              >
                Install
              </button>
            </article>
          ))}
        </div>
      )}
      {tab === "studio" && (
        <div className="studio-grid">
          <aside className="panel node-palette">
            <p className="eyebrow">BUILDING BLOCKS</p>
            {[
              "CareerPilot action",
              "AI step",
              "Condition",
              "Approval",
              "Integration",
            ].map((item) => (
              <button type="button" key={item}>
                + {item}
              </button>
            ))}
          </aside>
          <section className="panel workflow-canvas">
            <div className="workflow-node ai-node">AI · Tailor resume</div>
            <span>↓</span>
            <div className="workflow-node approval-node">
              Approval · Verify claims
            </div>
            <span>↓</span>
            <div className="workflow-node">Action · Prepare application</div>
            <button
              className="button"
              type="button"
              onClick={() => void createWorkflow()}
            >
              Save workflow
            </button>
          </section>
          <aside className="panel">
            <p className="eyebrow">WORKFLOWS</p>
            {workflows.map((item) => (
              <p key={item.id}>
                <strong>{item.name}</strong>
                <br />
                <small>Version {item.version}</small>
              </p>
            ))}
          </aside>
        </div>
      )}
      {tab === "packages" && (
        <section className="panel">
          <p className="eyebrow">PACKAGE MANAGER</p>
          <h2>Installed extensions</h2>
          {installations.length === 0 ? (
            <p className="empty">No packages installed.</p>
          ) : (
            installations.map((item) => (
              <div className="history-row" key={item.id}>
                <strong>{item.package_slug}</strong>
                <span>v{item.installed_version}</span>
                <em>{item.enabled ? "enabled" : "disabled"}</em>
              </div>
            ))
          )}
        </section>
      )}
      {tab === "publisher" && (
        <section className="panel">
          <p className="eyebrow">PUBLISHER CONSOLE</p>
          <h2>Ship trusted extensions</h2>
          <p className="muted">
            Semantic versions, explicit permissions, dependencies, signatures,
            and stable/beta/canary channels are required.
          </p>
          <div className="package-policy">
            <strong>✓ Manifest validation</strong>
            <strong>✓ Content signature</strong>
            <strong>✓ Least-privilege sandbox</strong>
            <strong>✓ Update channels</strong>
          </div>
        </section>
      )}
    </section>
  );
}
