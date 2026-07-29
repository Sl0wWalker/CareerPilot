import { useEffect, useState } from "react";

type ApiState = "checking" | "online" | "offline";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function App() {
  const [apiState, setApiState] = useState<ApiState>("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("API health check failed");
        setApiState("online");
      })
      .catch(() => setApiState("offline"));
    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">CP</span>
          <span>CareerPilot</span>
        </div>
        <div className={`status status-${apiState}`} aria-live="polite">
          <span className="status-dot" />
          Local service {apiState}
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">MILESTONE 0 · LOCAL FOUNDATION</p>
        <h1>Your job application workspace starts here.</h1>
        <p className="lede">
          CareerPilot is ready for the next milestone: building a verified
          career profile. Job discovery, AI, and autofill are intentionally not
          active yet.
        </p>
      </section>

      <section className="grid" aria-label="Foundation status">
        <article className="card card-accent">
          <span className="card-index">01</span>
          <h2>Private by default</h2>
          <p>Your local database and files stay on this computer.</p>
        </article>
        <article className="card">
          <span className="card-index">02</span>
          <h2>API ready</h2>
          <p>
            FastAPI, SQLite, migrations, configuration, and health checks are
            connected.
          </p>
        </article>
        <article className="card">
          <span className="card-index">03</span>
          <h2>Built to grow</h2>
          <p>
            The foundation keeps later profile, resume, matching, and automation
            work separate.
          </p>
        </article>
      </section>
    </main>
  );
}
