import { useCallback, useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type DocumentVersion = {
  id: string;
  title: string;
  document_type: string;
  version: number;
  status: string;
  content: Record<string, unknown>;
  keyword_coverage: { matched?: string[]; missing?: string[] };
};

export function DocumentWorkspace() {
  const [documents, setDocuments] = useState<DocumentVersion[]>([]);
  const [jobId, setJobId] = useState("");
  const [selected, setSelected] = useState<DocumentVersion | null>(null);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/documents`);
    if (response.ok) setDocuments(await response.json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function generate(kind: "resume" | "cover-letter") {
    if (!jobId.trim()) {
      setMessage("Choose a matched job first.");
      return;
    }
    const response = await fetch(
      `${API_BASE_URL}/documents/jobs/${jobId}/${kind}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          kind === "resume"
            ? { use_ai: true }
            : { use_ai: true, tone: "professional" },
        ),
      },
    );
    const body = await response.json();
    if (!response.ok) {
      setMessage(body.detail ?? "Generation failed.");
      return;
    }
    setSelected(body);
    setMessage("Draft created. Review and approve it before use.");
    await load();
  }

  async function approve() {
    if (!selected) return;
    const response = await fetch(`${API_BASE_URL}/documents/${selected.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "approved" }),
    });
    if (response.ok) {
      setSelected(await response.json());
      setMessage("Document approved.");
      await load();
    }
  }

  return (
    <section className="review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">DOCUMENT STUDIO</p>
          <h1>Tailor with evidence, then review.</h1>
        </div>
      </div>
      <div className="workspace">
        <article className="dropzone">
          <h2>Create a job-specific draft</h2>
          <p>Enter a job ID whose M5 match analysis is complete.</p>
          <input
            aria-label="Job ID"
            value={jobId}
            onChange={(event) => setJobId(event.target.value)}
            placeholder="Job ID"
          />
          <div className="fact-actions">
            <button type="button" onClick={() => void generate("resume")}>
              Tailor resume
            </button>
            <button type="button" onClick={() => void generate("cover-letter")}>
              Draft cover letter
            </button>
          </div>
          <p aria-live="polite">{message}</p>
        </article>
        <aside className="history">
          <div className="section-heading">
            <h2>Resume versions</h2>
            <span>{documents.length}</span>
          </div>
          {documents.map((document) => (
            <button
              type="button"
              className="history-row"
              key={document.id}
              onClick={() => setSelected(document)}
            >
              <strong>{document.title}</strong>
              <span>
                {document.document_type.replace("_", " ")} · v{document.version}
              </span>
              <em>{document.status}</em>
            </button>
          ))}
        </aside>
      </div>
      {selected && (
        <article className="fact">
          <div className="section-heading">
            <div>
              <p className="eyebrow">DOCUMENT COMPARISON & REVIEW</p>
              <h2>{selected.title}</h2>
            </div>
            <div className="fact-actions">
              <a
                className="button"
                href={`${API_BASE_URL}/documents/${selected.id}/export?format=pdf`}
              >
                Export PDF
              </a>
              <a
                className="button"
                href={`${API_BASE_URL}/documents/${selected.id}/export?format=docx`}
              >
                Export DOCX
              </a>
              <button
                type="button"
                className="accept"
                onClick={() => void approve()}
              >
                Approve
              </button>
            </div>
          </div>
          <pre>{JSON.stringify(selected.content, null, 2)}</pre>
          <p>
            Matched keywords:{" "}
            {selected.keyword_coverage.matched?.join(", ") || "None"}
          </p>
          <p>
            Missing keywords:{" "}
            {selected.keyword_coverage.missing?.join(", ") || "None"}
          </p>
        </article>
      )}
    </section>
  );
}
