import { useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type MaintenanceStatus = {
  version: string;
  governance_documents: Record<string, boolean>;
  quality_commands: string[];
  compatibility_policy: string;
  security_reporting: string;
};

export function MaintenanceWorkspace() {
  const [status, setStatus] = useState<MaintenanceStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/maintenance/status`)
      .then(async (response) => {
        if (!response.ok) throw new Error("Maintenance status is unavailable.");
        return response.json();
      })
      .then(setStatus)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return (
    <section className="release-workspace">
      <div className="hero compact-hero">
        <p className="eyebrow">PROJECT HEALTH</p>
        <h1>Maintenance and governance</h1>
        <p className="lede">
          Compatibility, security reporting, quality gates, and project policy
          in one place.
        </p>
      </div>
      {status ? (
        <div className="release-grid">
          <article className="panel">
            <p className="eyebrow">GOVERNANCE</p>
            <h2>Required policies</h2>
            <ul className="help-list">
              {Object.entries(status.governance_documents).map(
                ([document, present]) => (
                  <li key={document}>
                    {present ? "Ready" : "Missing"} — {document}
                  </li>
                ),
              )}
            </ul>
          </article>
          <article className="panel">
            <p className="eyebrow">QUALITY GATES</p>
            <h2>Version {status.version}</h2>
            <ul className="help-list">
              {status.quality_commands.map((command) => (
                <li key={command}>
                  <code>{command}</code>
                </li>
              ))}
            </ul>
          </article>
          <article className="panel">
            <p className="eyebrow">COMPATIBILITY</p>
            <p>{status.compatibility_policy}</p>
          </article>
          <article className="panel">
            <p className="eyebrow">SECURITY</p>
            <p>{status.security_reporting}</p>
          </article>
        </div>
      ) : (
        <p className={error ? "warning-text" : "muted"}>
          {error || "Checking project health..."}
        </p>
      )}
    </section>
  );
}
