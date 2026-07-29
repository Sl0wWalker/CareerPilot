import { useCallback, useEffect, useState } from "react";

type Health = {
  provider: string;
  model: string;
  available: boolean;
  detail: string;
};
type Suggestion = {
  id: string;
  suggestion_type: string;
  status: string;
  proposed: Record<string, unknown>;
  rationale: string;
  confidence: number;
};
type SearchResult = {
  entity_type: string;
  entity_id: string;
  text: string;
  score: number;
};
type Settings = {
  provider: "ollama" | "gemini" | "openai_compatible";
  model: string;
  embedding_model: string;
  base_url: string;
  temperature: number;
  max_tokens: number;
};

const API = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function AIWorkspace() {
  const [health, setHealth] = useState<Health | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [summary, setSummary] = useState<Record<string, string> | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    try {
      const responses = await Promise.all([
        fetch(`${API}/ai/health`),
        fetch(`${API}/ai/suggestions`),
        fetch(`${API}/ai/settings`),
      ]);
      if (responses[0].ok) setHealth(await responses[0].json());
      if (responses[1].ok) setSuggestions(await responses[1].json());
      if (responses[2].ok) setSettings(await responses[2].json());
    } catch {
      setHealth({
        provider: "ollama",
        model: "Unavailable",
        available: false,
        detail: "Local API offline",
      });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(path: string) {
    setBusy(true);
    setMessage("");
    const response = await fetch(`${API}${path}`, { method: "POST" });
    const body = await response.json();
    setBusy(false);
    if (!response.ok) {
      setMessage(body.detail ?? "AI request failed.");
    } else if (path.endsWith("summarize")) {
      setSummary(body);
    } else {
      setSuggestions(body);
      setMessage("Suggestions are ready for review.");
    }
  }

  async function review(id: string, status: "approved" | "rejected") {
    await fetch(`${API}/ai/suggestions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    await load();
  }

  async function search() {
    const response = await fetch(`${API}/ai/profile/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit: 10 }),
    });
    if (response.ok) setResults(await response.json());
    else
      setMessage(
        "Create a profile and install the configured embedding model first.",
      );
  }

  async function saveSettings() {
    if (!settings) return;
    const response = await fetch(`${API}/ai/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    setMessage(
      response.ok ? "AI preferences saved." : "Could not save settings.",
    );
  }

  return (
    <section className="ai-workspace">
      <div className="ai-grid">
        <article className="panel">
          <p className="eyebrow">LOCAL AI</p>
          <h2>{health?.model ?? "Checking model…"}</h2>
          <p className={health?.available ? "good" : "muted"}>
            {health?.available
              ? "Ready"
              : (health?.detail ?? "Checking Ollama")}
          </p>
          <div className="action-row">
            <button
              type="button"
              className="button"
              disabled={busy}
              onClick={() => void run("/ai/profile/enrich")}
            >
              Analyze profile
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void run("/ai/profile/summarize")}
            >
              Draft summaries
            </button>
          </div>
          {message && <p className="muted">{message}</p>}
        </article>
        <article className="panel">
          <p className="eyebrow">SEMANTIC SEARCH</p>
          <h2>Find your strongest evidence</h2>
          <div className="search-row">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="e.g. automation leadership"
            />
            <button
              type="button"
              className="button"
              onClick={() => void search()}
            >
              Search
            </button>
          </div>
          {results.map((result) => (
            <div
              className="search-result"
              key={`${result.entity_type}-${result.entity_id}`}
            >
              <strong>{result.entity_type}</strong>
              <span>{Math.round(result.score * 100)}%</span>
              <p>{result.text}</p>
            </div>
          ))}
        </article>
      </div>
      {summary && (
        <section className="panel summary-grid">
          {Object.entries(summary).map(([name, text]) => (
            <article key={name}>
              <strong>{name}</strong>
              <p>{text}</p>
            </article>
          ))}
        </section>
      )}
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">REVIEW REQUIRED</p>
            <h2>AI suggestions</h2>
          </div>
          <span>
            {suggestions.filter((item) => item.status === "pending").length}
          </span>
        </div>
        <div className="suggestions">
          {suggestions.length === 0 && (
            <p className="empty">Run profile analysis to create suggestions.</p>
          )}
          {suggestions.map((item) => (
            <article className="suggestion" key={item.id}>
              <div>
                <strong>{item.suggestion_type.replaceAll("_", " ")}</strong>
                <span>{Math.round(item.confidence * 100)}%</span>
              </div>
              <p>{item.rationale}</p>
              <pre>{JSON.stringify(item.proposed, null, 2)}</pre>
              {item.status === "pending" ? (
                <div className="action-row">
                  <button
                    type="button"
                    className="accept"
                    onClick={() => void review(item.id, "approved")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="reject"
                    onClick={() => void review(item.id, "rejected")}
                  >
                    Reject
                  </button>
                </div>
              ) : (
                <em>{item.status}</em>
              )}
            </article>
          ))}
        </div>
      </section>
      {settings && (
        <section className="panel settings-form">
          <p className="eyebrow">AI SETTINGS</p>
          <h2>Provider configuration</h2>
          <div className="form-grid">
            <label>
              Provider
              <select
                value={settings.provider}
                onChange={(event) =>
                  setSettings({
                    ...settings,
                    provider: event.target.value as Settings["provider"],
                  })
                }
              >
                <option value="ollama">Ollama</option>
                <option value="gemini">Gemini</option>
                <option value="openai_compatible">OpenAI-compatible</option>
              </select>
            </label>
            <label>
              Model
              <input
                value={settings.model}
                onChange={(event) =>
                  setSettings({ ...settings, model: event.target.value })
                }
              />
            </label>
            <label>
              Embedding model
              <input
                value={settings.embedding_model}
                onChange={(event) =>
                  setSettings({
                    ...settings,
                    embedding_model: event.target.value,
                  })
                }
              />
            </label>
            <label>
              Base URL
              <input
                value={settings.base_url}
                onChange={(event) =>
                  setSettings({ ...settings, base_url: event.target.value })
                }
              />
            </label>
          </div>
          <button
            type="button"
            className="button"
            onClick={() => void saveSettings()}
          >
            Save preferences
          </button>
          <p className="muted">
            Secrets stay in your local environment and are never stored here.
          </p>
        </section>
      )}
    </section>
  );
}
