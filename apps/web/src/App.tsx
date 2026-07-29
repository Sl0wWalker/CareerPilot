import {
  type ChangeEvent,
  type DragEvent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { AIWorkspace } from "./AIWorkspace";

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
  const [view, setView] = useState<"resume" | "ai">("resume");
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
          <span>CareerPilot</span>
        </div>
        <div className={`status status-${apiState}`} aria-live="polite">
          <span className="status-dot" />
          Local service {apiState}
        </div>
      </header>
      <nav className="view-tabs" aria-label="Workspace">
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

      {view === "ai" ? (
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
