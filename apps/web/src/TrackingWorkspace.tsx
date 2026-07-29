import { useCallback, useEffect, useMemo, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const columns = [
  "draft",
  "preparing",
  "ready",
  "submitted",
  "recruiter_screen",
  "interview",
  "offer",
  "rejected",
] as const;

type Application = {
  id: string;
  job_id: string;
  status: string;
  source: string;
  tags: string[];
  applied_at: string | null;
  updated_at: string;
};
type Analytics = {
  total: number;
  submitted: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  average_days_to_response: number | null;
  by_status: Record<string, number>;
};
type Event = {
  id: string;
  title: string;
  occurred_at: string;
  to_status: string | null;
};
type Note = { id: string; body: string; pinned: boolean };
type Contact = {
  id: string;
  name: string;
  role: string | null;
  email: string | null;
};

export function TrackingWorkspace() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [selected, setSelected] = useState<Application | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filter, setFilter] = useState("");

  const load = useCallback(async () => {
    const [apps, metrics] = await Promise.all([
      fetch(`${API}/applications`),
      fetch(`${API}/applications/analytics`),
    ]);
    if (apps.ok) setApplications(await apps.json());
    if (metrics.ok) setAnalytics(await metrics.json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function select(item: Application) {
    setSelected(item);
    const [timeline, noteList, contactList] = await Promise.all([
      fetch(`${API}/applications/${item.id}/timeline`),
      fetch(`${API}/applications/${item.id}/notes`),
      fetch(`${API}/applications/${item.id}/contacts`),
    ]);
    if (timeline.ok) setEvents(await timeline.json());
    if (noteList.ok) setNotes(await noteList.json());
    if (contactList.ok) setContacts(await contactList.json());
  }

  async function move(item: Application, status: string) {
    const response = await fetch(`${API}/applications/${item.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (response.ok) {
      const updated = await response.json();
      await load();
      if (selected?.id === item.id) await select(updated);
    }
  }

  async function addNote(body: string) {
    if (!selected || !body.trim()) return;
    const response = await fetch(`${API}/applications/${selected.id}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body, pinned: false }),
    });
    if (response.ok) {
      const note = await response.json();
      setNotes((current) => [note, ...current]);
    }
  }

  const visible = useMemo(
    () =>
      applications.filter((item) =>
        `${item.job_id} ${item.tags.join(" ")}`
          .toLowerCase()
          .includes(filter.toLowerCase()),
      ),
    [applications, filter],
  );

  return (
    <section className="tracking-workspace">
      <div className="tracking-head">
        <div>
          <p className="eyebrow">APPLICATION OPERATIONS</p>
          <h1>Keep every opportunity moving.</h1>
        </div>
        <a className="button export-link" href={`${API}/applications/export`}>
          Export JSON
        </a>
      </div>
      <div className="metric-grid">
        <Metric label="Applications" value={analytics?.total ?? 0} />
        <Metric label="Submitted" value={analytics?.submitted ?? 0} />
        <Metric
          label="Response rate"
          value={`${analytics?.response_rate ?? 0}%`}
        />
        <Metric
          label="Interview rate"
          value={`${analytics?.interview_rate ?? 0}%`}
        />
        <Metric label="Offer rate" value={`${analytics?.offer_rate ?? 0}%`} />
        <Metric
          label="Days to response"
          value={analytics?.average_days_to_response ?? "—"}
        />
      </div>
      <div className="tracking-toolbar panel">
        <input
          aria-label="Filter applications"
          placeholder="Filter by job ID or tag"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        />
        <span>{visible.length} visible</span>
      </div>
      <section className="kanban" aria-label="Application Kanban board">
        {columns.map((status) => (
          <ul
            className="kanban-column"
            key={status}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              const item = applications.find(
                (candidate) =>
                  candidate.id === event.dataTransfer.getData("application"),
              );
              if (item) void move(item, status);
            }}
          >
            <header>
              <strong>{status.replaceAll("_", " ")}</strong>
              <span>
                {visible.filter((item) => item.status === status).length}
              </span>
            </header>
            {visible
              .filter((item) => item.status === status)
              .map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    draggable
                    className="application-card"
                    onDragStart={(event) =>
                      event.dataTransfer.setData("application", item.id)
                    }
                    onClick={() => void select(item)}
                  >
                    <strong>Job {item.job_id.slice(0, 8)}</strong>
                    <small>
                      {item.source} ·{" "}
                      {new Date(item.updated_at).toLocaleDateString()}
                    </small>
                    <div>
                      {item.tags.map((tag) => (
                        <span key={tag}>{tag}</span>
                      ))}
                    </div>
                  </button>
                </li>
              ))}
          </ul>
        ))}
      </section>
      {selected && (
        <div className="tracking-detail">
          <section className="panel">
            <p className="eyebrow">TIMELINE</p>
            <h2>Application history</h2>
            {events.map((event) => (
              <article className="timeline-row" key={event.id}>
                <span />
                <div>
                  <strong>{event.title}</strong>
                  <small>{new Date(event.occurred_at).toLocaleString()}</small>
                </div>
              </article>
            ))}
          </section>
          <section className="panel">
            <p className="eyebrow">NOTES & CONTACTS</p>
            <h2>Relationship context</h2>
            <NoteComposer onAdd={addNote} />
            {notes.map((note) => (
              <p className="note" key={note.id}>
                {note.body}
              </p>
            ))}
            {contacts.map((contact) => (
              <p className="contact" key={contact.id}>
                <strong>{contact.name}</strong> {contact.role ?? ""}
                <br />
                <small>{contact.email}</small>
              </p>
            ))}
          </section>
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function NoteComposer({ onAdd }: { onAdd: (body: string) => Promise<void> }) {
  const [body, setBody] = useState("");
  return (
    <div className="note-composer">
      <input
        aria-label="New note"
        placeholder="Add a note"
        value={body}
        onChange={(event) => setBody(event.target.value)}
      />
      <button
        type="button"
        onClick={() => {
          void onAdd(body);
          setBody("");
        }}
      >
        Add
      </button>
    </div>
  );
}
