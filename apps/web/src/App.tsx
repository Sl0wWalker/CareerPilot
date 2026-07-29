import {
  type ChangeEvent,
  type DragEvent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { AIWorkspace } from "./AIWorkspace";
import { AutomationWorkspace } from "./AutomationWorkspace";
import { BetaWorkspace } from "./BetaWorkspace";
import { CoachWorkspace } from "./CoachWorkspace";
import { DeveloperWorkspace } from "./DeveloperWorkspace";
import { DocumentWorkspace } from "./DocumentWorkspace";
import { EnterpriseWorkspace } from "./EnterpriseWorkspace";
import { GlobalWorkspace } from "./GlobalWorkspace";
import { IntelligenceWorkspace } from "./IntelligenceWorkspace";
import { t } from "./i18n";
import { JobWorkspace } from "./JobWorkspace";
import { MarketplaceWorkspace } from "./MarketplaceWorkspace";
import { ReleaseWorkspace } from "./ReleaseWorkspace";
import { SyncWorkspace } from "./SyncWorkspace";
import { TrackingWorkspace } from "./TrackingWorkspace";

type ApiState = "checking" | "online" | "offline";
type UploadState = "idle" | "uploading" | "complete" | "error";

type ParsedFact = {
  id: string;
  entity_type: string;
  payload: Record<string, unknown>;
  confidence: number;
  approved: boolean;
  rejected: boolean;
  source_reference: string;
};

type ResumeImport = {
  id: string;
  filename: string;
  parser_version: string;
  parsing_status: string;
  created_at: string;
  warnings: string[];
  facts?: ParsedFact[];
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function App() {
  const [view, setView] = useState<
    | "resume"
    | "ai"
    | "jobs"
    | "documents"
    | "automation"
    | "tracking"
    | "beta"
    | "start"
    | "sync"
    | "coach"
    | "developer"
    | "enterprise"
    | "marketplace"
    | "intelligence"
    | "global"
  >("start");
  const [showOnboarding, setShowOnboarding] = useState(
    () => localStorage.getItem("careerpilot.onboarding.complete") !== "true",
  );
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [message, setMessage] = useState("");
  const [imports, setImports] = useState<ResumeImport[]>([]);
  const [selected, setSelected] = useState<ResumeImport | null>(null);
  const [dragging, setDragging] = useState(false);

  const loadImports = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/resume/imports`);
    if (response.ok) setImports(await response.json());
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("API health check failed");
        setApiState("online");
        return loadImports();
      })
      .catch(() => setApiState("offline"));
    return () => controller.abort();
  }, [loadImports]);

  async function upload(file: File) {
    setUploadState("uploading");
    setMessage(`Reading ${file.name}…`);
    const response = await fetch(
      `${API_BASE_URL}/resume/import?filename=${encodeURIComponent(file.name)}`,
      { method: "POST", headers: { "Content-Type": file.type }, body: file },
    );
    const body = await response.json();
    if (!response.ok) {
      setUploadState("error");
      setMessage(
        typeof body.detail === "string"
          ? body.detail
          : (body.detail?.message ?? "Upload failed"),
      );
      return;
    }
    setUploadState("complete");
    setMessage("Import complete. Review the extracted facts below.");
    setSelected(body);
    await loadImports();
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) void upload(file);
  }

  function dropFile(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) void upload(file);
  }

  async function openReview(importId: string) {
    const response = await fetch(
      `${API_BASE_URL}/resume/import/${importId}/review`,
    );
    if (response.ok) setSelected(await response.json());
  }

  async function updateFact(
    fact: ParsedFact,
    change: Partial<Pick<ParsedFact, "payload" | "approved" | "rejected">>,
  ) {
    if (!selected) return;
    const response = await fetch(
      `${API_BASE_URL}/resume/import/${selected.id}/fact/${fact.id}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(change),
      },
    );
    if (response.ok) setSelected(await response.json());
  }

  async function approveImport() {
    if (!selected) return;
    const response = await fetch(
      `${API_BASE_URL}/resume/import/${selected.id}/approve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fact_ids: null }),
      },
    );
    if (response.ok) {
      setSelected(await response.json());
      setMessage("Approved facts were added to your Career Knowledge Base.");
      await loadImports();
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">CP</span>
          <span>{t("appName")}</span>
        </div>
        <div className={`status status-${apiState}`} aria-live="polite">
          <span className="status-dot" />
          {t("localService")} {apiState}
        </div>
      </header>
      <nav className="view-tabs" aria-label={t("workspace")}>
        <button
          type="button"
          className={view === "global" ? "active" : ""}
          onClick={() => setView("global")}
        >
          Global & mobile
        </button>
        <button
          type="button"
          className={view === "intelligence" ? "active" : ""}
          onClick={() => setView("intelligence")}
        >
          Career intelligence
        </button>
        <button
          type="button"
          className={view === "marketplace" ? "active" : ""}
          onClick={() => setView("marketplace")}
        >
          Marketplace
        </button>
        <button
          type="button"
          className={view === "enterprise" ? "active" : ""}
          onClick={() => setView("enterprise")}
        >
          Enterprise
        </button>
        <button
          type="button"
          className={view === "developer" ? "active" : ""}
          onClick={() => setView("developer")}
        >
          Developer
        </button>
        <button
          type="button"
          className={view === "coach" ? "active" : ""}
          onClick={() => setView("coach")}
        >
          Career coach
        </button>
        <button
          type="button"
          className={view === "sync" ? "active" : ""}
          onClick={() => setView("sync")}
        >
          Sync & integrations
        </button>
        <button
          type="button"
          className={view === "beta" ? "active" : ""}
          onClick={() => setView("beta")}
        >
          Beta & feedback
        </button>
        <button
          type="button"
          className={view === "start" ? "active" : ""}
          onClick={() => setView("start")}
        >
          Start & help
        </button>
        <button
          type="button"
          className={view === "tracking" ? "active" : ""}
          onClick={() => setView("tracking")}
        >
          Applications
        </button>
        <button
          type="button"
          className={view === "automation" ? "active" : ""}
          onClick={() => setView("automation")}
        >
          Application automation
        </button>
        <button
          type="button"
          className={view === "documents" ? "active" : ""}
          onClick={() => setView("documents")}
        >
          Document studio
        </button>
        <button
          type="button"
          className={view === "jobs" ? "active" : ""}
          onClick={() => setView("jobs")}
        >
          Job discovery
        </button>
        <button
          type="button"
          className={view === "ai" ? "active" : ""}
          onClick={() => setView("ai")}
        >
          AI intelligence
        </button>
        <button
          type="button"
          className={view === "resume" ? "active" : ""}
          onClick={() => setView("resume")}
        >
          Resume imports
        </button>
      </nav>

      {showOnboarding ? (
        <FirstRun
          onComplete={() => {
            localStorage.setItem("careerpilot.onboarding.complete", "true");
            setShowOnboarding(false);
            setView("resume");
          }}
        />
      ) : view === "global" ? (
        <GlobalWorkspace />
      ) : view === "start" ? (
        <ReleaseWorkspace onRestartOnboarding={() => setShowOnboarding(true)} />
      ) : view === "tracking" ? (
        <TrackingWorkspace />
      ) : view === "developer" ? (
        <DeveloperWorkspace />
      ) : view === "enterprise" ? (
        <EnterpriseWorkspace />
      ) : view === "marketplace" ? (
        <MarketplaceWorkspace />
      ) : view === "intelligence" ? (
        <IntelligenceWorkspace />
      ) : view === "coach" ? (
        <CoachWorkspace />
      ) : view === "sync" ? (
        <SyncWorkspace />
      ) : view === "beta" ? (
        <BetaWorkspace />
      ) : view === "automation" ? (
        <AutomationWorkspace />
      ) : view === "documents" ? (
        <DocumentWorkspace />
      ) : view === "jobs" ? (
        <JobWorkspace />
      ) : view === "ai" ? (
        <AIWorkspace />
      ) : (
        <>
          <section className="hero">
            <p className="eyebrow">CAREER KNOWLEDGE</p>
            <h1>Turn your resume into trusted career data.</h1>
            <p className="lede">
              Upload a PDF, DOCX, or TXT resume. CareerPilot extracts facts
              locally, shows its evidence, and waits for your approval.
            </p>
          </section>

          <section className="workspace">
            <label
              className={`dropzone ${dragging ? "dropzone-active" : ""}`}
              htmlFor="resume-file"
              onDragEnter={() => setDragging(true)}
              onDragLeave={() => setDragging(false)}
              onDragOver={(event) => event.preventDefault()}
              onDrop={dropFile}
            >
              <span className="drop-icon">↥</span>
              <h2>Import your resume</h2>
              <p>Drop a file here or choose one from your computer.</p>
              <span className="button">Choose resume</span>
              <input
                id="resume-file"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={chooseFile}
              />
              {uploadState !== "idle" && (
                <div
                  className={`upload-state upload-${uploadState}`}
                  aria-live="polite"
                >
                  <span className="progress">
                    <span />
                  </span>
                  {message}
                </div>
              )}
            </label>

            <aside className="history">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">IMPORT HISTORY</p>
                  <h2>Recent resumes</h2>
                </div>
                <span>{imports.length}</span>
              </div>
              {imports.length === 0 ? (
                <p className="empty">No resumes imported yet.</p>
              ) : (
                imports.map((item) => (
                  <button
                    type="button"
                    className="history-row"
                    key={item.id}
                    onClick={() => void openReview(item.id)}
                  >
                    <strong>{item.filename}</strong>
                    <span>
                      {new Date(item.created_at).toLocaleDateString()} ·{" "}
                      {item.parser_version}
                    </span>
                    <em>{item.parsing_status.replace("_", " ")}</em>
                  </button>
                ))
              )}
            </aside>
          </section>

          {selected && (
            <section className="review">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">REVIEW QUEUE</p>
                  <h2>{selected.filename}</h2>
                </div>
                <button
                  type="button"
                  className="button"
                  onClick={() => void approveImport()}
                >
                  Approve accepted facts
                </button>
              </div>
              {selected.warnings.length > 0 && (
                <div className="warnings">
                  {selected.warnings.map((warning) => (
                    <p key={warning}>⚠ {warning}</p>
                  ))}
                </div>
              )}
              <div className="facts">
                {(selected.facts ?? []).map((fact) => (
                  <FactCard key={fact.id} fact={fact} onUpdate={updateFact} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}

function FirstRun({ onComplete }: { onComplete: () => void }) {
  return (
    <section className="first-run" aria-labelledby="first-run-title">
      <p className="eyebrow">WELCOME TO CAREERPILOT</p>
      <h1 id="first-run-title">Your application copilot, on your computer.</h1>
      <p className="lede">
        CareerPilot turns verified career facts into job matches, tailored
        documents, and supervised application autofill.
      </p>
      <div className="onboarding-grid">
        <article className="panel">
          <strong className="step-number">1</strong>
          <h2>Build your fact bank</h2>
          <p className="muted">
            Import a resume and approve only accurate facts.
          </p>
        </article>
        <article className="panel">
          <strong className="step-number">2</strong>
          <h2>Find the right jobs</h2>
          <p className="muted">
            Use explainable matching, not opaque AI scores.
          </p>
        </article>
        <article className="panel">
          <strong className="step-number">3</strong>
          <h2>Apply with control</h2>
          <p className="muted">
            Autofill routine fields and review before submit.
          </p>
        </article>
      </div>
      <div className="onboarding-actions">
        <button type="button" className="button" onClick={onComplete}>
          Start with my resume
        </button>
        <span>No account or paid API required for local use.</span>
      </div>
    </section>
  );
}

function FactCard({
  fact,
  onUpdate,
}: {
  fact: ParsedFact;
  onUpdate: (
    fact: ParsedFact,
    change: Partial<Pick<ParsedFact, "payload" | "approved" | "rejected">>,
  ) => Promise<void>;
}) {
  const [draft, setDraft] = useState(JSON.stringify(fact.payload, null, 2));

  return (
    <article className={`fact ${fact.rejected ? "fact-rejected" : ""}`}>
      <div className="fact-meta">
        <strong>{fact.entity_type}</strong>
        <span>{Math.round(fact.confidence * 100)}% confidence</span>
        <span>{fact.source_reference}</span>
      </div>
      <textarea
        aria-label={`Edit ${fact.entity_type} fact`}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      <div className="fact-actions">
        <button
          type="button"
          onClick={() => void onUpdate(fact, { payload: JSON.parse(draft) })}
        >
          Save edit
        </button>
        <button
          type="button"
          className="accept"
          onClick={() =>
            void onUpdate(fact, { approved: true, rejected: false })
          }
        >
          Accept
        </button>
        <button
          type="button"
          className="reject"
          onClick={() =>
            void onUpdate(fact, { rejected: true, approved: false })
          }
        >
          Reject
        </button>
      </div>
    </article>
  );
}
