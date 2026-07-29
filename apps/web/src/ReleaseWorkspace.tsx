import { useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type Diagnostics = {
  version: string;
  environment: string;
  database: string;
  authentication: boolean;
};

export function ReleaseWorkspace({
  onRestartOnboarding,
}: {
  onRestartOnboarding: () => void;
}) {
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/diagnostics`)
      .then(async (response) => {
        if (!response.ok) throw new Error("Diagnostics are unavailable.");
        return response.json();
      })
      .then(setDiagnostics)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return (
    <section className="release-workspace">
      <div className="hero compact-hero">
        <p className="eyebrow">CAREERPILOT V1</p>
        <h1>Ready when you are.</h1>
        <p className="lede">
          Review local services, privacy controls, backups, and the safest path
          through your first application.
        </p>
      </div>

      <div className="release-grid">
        <article className="panel">
          <p className="eyebrow">SYSTEM CHECK</p>
          {diagnostics ? (
            <dl className="diagnostic-list">
              <div>
                <dt>Version</dt>
                <dd>{diagnostics.version}</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>{diagnostics.environment}</dd>
              </div>
              <div>
                <dt>Database</dt>
                <dd>{diagnostics.database}</dd>
              </div>
              <div>
                <dt>Authentication</dt>
                <dd>{diagnostics.authentication ? "enabled" : "local mode"}</dd>
              </div>
            </dl>
          ) : (
            <p className={error ? "warning-text" : "muted"}>
              {error || "Checking local services..."}
            </p>
          )}
        </article>

        <article className="panel">
          <p className="eyebrow">PRIVACY & CONTROL</p>
          <h2>Local-first by default</h2>
          <ul className="help-list">
            <li>Career data and SQLite records stay on this device.</li>
            <li>Ollama is the default AI provider.</li>
            <li>Application automation pauses for human review.</li>
            <li>CAPTCHAs and legal attestations always require you.</li>
          </ul>
        </article>

        <article className="panel">
          <p className="eyebrow">QUICK START</p>
          <ol className="help-list">
            <li>Import and approve your resume facts.</li>
            <li>Confirm the local AI provider in AI Intelligence.</li>
            <li>Discover a job and review its match evidence.</li>
            <li>Create documents, then run automation in dry-run mode.</li>
            <li>Review every answer before submitting.</li>
          </ol>
        </article>

        <article className="panel">
          <p className="eyebrow">RECOVERY</p>
          <h2>Back up before important changes</h2>
          <p className="muted">
            Use the included backup and restore scripts. Restore operations
            validate that the selected file is inside the backup directory.
          </p>
          <button type="button" onClick={onRestartOnboarding}>
            Restart first-run guide
          </button>
        </article>
      </div>
    </section>
  );
}
