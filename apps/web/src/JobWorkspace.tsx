import { useCallback, useEffect, useState } from "react";

type Job = {
  id: string;
  title: string;
  company_name: string;
  source_provider: string;
  canonical_url: string;
  description: string;
  location_raw: string | null;
  workplace_type: string;
  employment_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  is_favorite: boolean;
  relevance_score: number | null;
  relevance_analysis: {
    strengths?: string[];
    gaps?: string[];
    reason?: string;
  } | null;
};

type SavedSearch = {
  id: string;
  name: string;
  query: string | null;
  filters: Record<string, unknown>;
};

const API = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function JobWorkspace() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [saved, setSaved] = useState<SavedSearch[]>([]);
  const [selected, setSelected] = useState<Job | null>(null);
  const [query, setQuery] = useState("");
  const [workplace, setWorkplace] = useState("");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [message, setMessage] = useState("");

  const search = useCallback(async () => {
    const response = await fetch(`${API}/jobs/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query || null,
        workplace_type: workplace || null,
        favorite_only: favoriteOnly,
      }),
    });
    if (response.ok) {
      const body: unknown = await response.json();
      setJobs(Array.isArray(body) ? body : []);
    }
  }, [favoriteOnly, query, workplace]);

  const loadSaved = useCallback(async () => {
    const response = await fetch(`${API}/jobs/saved-searches`);
    if (response.ok) {
      const body: unknown = await response.json();
      setSaved(Array.isArray(body) ? body : []);
    }
  }, []);

  useEffect(() => {
    void search();
    void loadSaved();
  }, [search, loadSaved]);

  async function toggleFavorite(job: Job) {
    const response = await fetch(`${API}/jobs/${job.id}/favorite`, {
      method: "PATCH",
    });
    if (response.ok) {
      const updated = await response.json();
      setSelected(updated);
      await search();
    }
  }

  async function analyze(job: Job) {
    setMessage("Analyzing this role with your verified profile…");
    const response = await fetch(`${API}/jobs/${job.id}/analyze`, {
      method: "POST",
    });
    const body = await response.json();
    setMessage(response.ok ? "Relevance analysis complete." : body.detail);
    if (response.ok) {
      setSelected(body);
      await search();
    }
  }

  async function saveSearch() {
    const name = query.trim() || "All jobs";
    const response = await fetch(`${API}/jobs/saved-searches`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        query: query || null,
        filters: {
          workplace_type: workplace || null,
          favorite_only: favoriteOnly,
        },
      }),
    });
    if (response.ok) {
      setMessage(
        "Search saved. Scheduling can be configured without running in background.",
      );
      await loadSaved();
    }
  }

  return (
    <section className="jobs-workspace">
      <section className="hero jobs-hero">
        <p className="eyebrow">INTELLIGENT DISCOVERY</p>
        <h1>Find jobs worth your time.</h1>
        <p className="lede">
          Search normalized listings, compare fit with verified career evidence,
          and keep promising roles close.
        </p>
      </section>
      <section className="job-toolbar panel">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Role, skill, or company"
        />
        <select
          value={workplace}
          onChange={(event) => setWorkplace(event.target.value)}
        >
          <option value="">Any workplace</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="onsite">On-site</option>
        </select>
        <label className="favorite-filter">
          <input
            type="checkbox"
            checked={favoriteOnly}
            onChange={(event) => setFavoriteOnly(event.target.checked)}
          />
          Favorites
        </label>
        <button type="button" className="button" onClick={() => void search()}>
          Search
        </button>
        <button type="button" onClick={() => void saveSearch()}>
          Save search
        </button>
      </section>
      {message && <p className="muted">{message}</p>}
      <section className="job-layout">
        <div className="job-list">
          {jobs.length === 0 && (
            <div className="panel empty">
              No jobs yet. Add and sync a source through the local API.
            </div>
          )}
          {jobs.map((job) => (
            <button
              type="button"
              className={`job-card ${selected?.id === job.id ? "selected" : ""}`}
              key={job.id}
              onClick={() => setSelected(job)}
            >
              <div>
                <span className="source-pill">{job.source_provider}</span>
                {job.relevance_score !== null && (
                  <span className="score">
                    {Math.round(job.relevance_score)}% fit
                  </span>
                )}
              </div>
              <h2>{job.title}</h2>
              <strong>{job.company_name}</strong>
              <p>
                {job.location_raw ?? "Location not listed"} ·{" "}
                {job.workplace_type}
              </p>
            </button>
          ))}
        </div>
        <aside className="panel job-detail">
          {selected ? (
            <>
              <div className="detail-actions">
                <button
                  type="button"
                  onClick={() => void toggleFavorite(selected)}
                >
                  {selected.is_favorite ? "★ Saved" : "☆ Save"}
                </button>
                <button
                  type="button"
                  className="button"
                  onClick={() => void analyze(selected)}
                >
                  Analyze relevance
                </button>
              </div>
              <p className="eyebrow">{selected.company_name}</p>
              <h2>{selected.title}</h2>
              <p>{selected.location_raw ?? "Location not listed"}</p>
              {selected.relevance_analysis && (
                <div className="relevance">
                  <strong>
                    {Math.round(selected.relevance_score ?? 0)}% relevance
                  </strong>
                  <p>{selected.relevance_analysis.reason}</p>
                  <div>
                    {(selected.relevance_analysis.strengths ?? []).map(
                      (item) => (
                        <span className="strength" key={item}>
                          + {item}
                        </span>
                      ),
                    )}
                    {(selected.relevance_analysis.gaps ?? []).map((item) => (
                      <span className="gap" key={item}>
                        − {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <p className="job-description">{selected.description}</p>
              <a className="button apply-link" href={selected.canonical_url}>
                View original job
              </a>
            </>
          ) : (
            <p className="empty">Choose a job to see its details.</p>
          )}
        </aside>
      </section>
      <section className="panel saved-searches">
        <div className="section-heading">
          <div>
            <p className="eyebrow">SAVED SEARCHES</p>
            <h2>Repeatable discovery definitions</h2>
          </div>
          <span>{saved.length}</span>
        </div>
        {saved.map((item) => (
          <button
            type="button"
            key={item.id}
            onClick={() => setQuery(item.query ?? "")}
          >
            <strong>{item.name}</strong>
            <span>{item.query ?? "All jobs"}</span>
          </button>
        ))}
      </section>
    </section>
  );
}
