import { type FormEvent, useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Device = {
  id: string;
  device_key: string;
  display_name: string;
  platform: string;
  last_seen_at: string | null;
  revoked: boolean;
};
type Integration = {
  provider: string;
  category: string;
  capabilities: string[];
  permitted_use: string;
  connected: boolean;
};
type Account = {
  id: string;
  provider: string;
  display_name: string;
  status: string;
  scopes_json: string[];
};
type Workspace = {
  id: string;
  owner_id: string;
  name: string;
  description: string;
};
type Conflict = {
  id: string;
  entity_type: string;
  entity_key: string;
  status: string;
};

export function SyncWorkspace() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    const paths = [
      "/api/v1/sync/devices",
      "/api/v1/sync/integrations",
      "/api/v1/sync/accounts",
      "/api/v1/sync/workspaces",
      "/api/v1/sync/conflicts",
    ];
    const responses = await Promise.all(paths.map((path) => apiFetch(path)));
    if (responses.every((response) => response.ok)) {
      const [
        nextDevices,
        nextIntegrations,
        nextAccounts,
        nextWorkspaces,
        nextConflicts,
      ] = await Promise.all(responses.map((response) => response.json()));
      setDevices(nextDevices);
      setIntegrations(nextIntegrations);
      setAccounts(nextAccounts);
      setWorkspaces(nextWorkspaces);
      setConflicts(nextConflicts);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function registerThisDevice() {
    const response = await apiFetch("/api/v1/sync/devices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_key:
          localStorage.getItem("careerpilot.device.key") ?? crypto.randomUUID(),
        display_name: navigator.platform || "CareerPilot browser",
        platform: navigator.userAgent.includes("Windows") ? "Windows" : "Web",
      }),
    });
    if (response.ok) {
      const device = await response.json();
      localStorage.setItem("careerpilot.device.key", device.device_key);
      setMessage("This device is ready for offline-first sync.");
      await refresh();
    }
  }

  async function createWorkspace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/sync/workspaces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.get("name"),
        description: data.get("description"),
      }),
    });
    if (response.ok) {
      event.currentTarget.reset();
      await refresh();
    }
  }

  async function createConnection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const provider = String(data.get("provider"));
    const response = await apiFetch("/api/v1/sync/accounts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider,
        external_account_id: data.get("account"),
        display_name: data.get("account"),
        scopes: ["import", "export"],
      }),
    });
    if (response.ok) {
      setMessage(
        "Connection saved as pending. Complete provider authorization when configured.",
      );
      event.currentTarget.reset();
      await refresh();
    }
  }

  async function resolveConflict(
    id: string,
    resolution: "keep_local" | "keep_remote",
  ) {
    const response = await apiFetch(`/api/v1/sync/conflicts/${id}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolution }),
    });
    if (response.ok) await refresh();
  }

  return (
    <section className="sync-workspace">
      <div className="hero compact-hero">
        <p className="eyebrow">SYNC & ECOSYSTEM</p>
        <h1>Your data, available where you choose.</h1>
        <p className="lede">
          CareerPilot remains local-first. Sync, collaboration, and integrations
          are optional, permission-scoped, and designed to recover gracefully
          offline.
        </p>
        {message && (
          <p className="good" role="status">
            {message}
          </p>
        )}
      </div>

      <div className="sync-grid">
        <article className="panel">
          <p className="eyebrow">SYNC CENTER</p>
          <div className="section-heading">
            <h2>Trusted devices</h2>
            <button
              className="button"
              type="button"
              onClick={() => void registerThisDevice()}
            >
              Register this device
            </button>
          </div>
          {devices.length === 0 ? (
            <p className="muted">No devices registered.</p>
          ) : (
            devices.map((device) => (
              <div className="sync-row" key={device.id}>
                <div>
                  <strong>{device.display_name}</strong>
                  <span>{device.platform}</span>
                </div>
                <em>{device.revoked ? "revoked" : "trusted"}</em>
              </div>
            ))
          )}
          <h3>Conflicts requiring review</h3>
          {conflicts.length === 0 ? (
            <p className="muted">Everything is synchronized.</p>
          ) : (
            conflicts.map((conflict) => (
              <div className="conflict-row" key={conflict.id}>
                <span>
                  {conflict.entity_type} · {conflict.entity_key}
                </span>
                <div>
                  <button
                    type="button"
                    onClick={() =>
                      void resolveConflict(conflict.id, "keep_local")
                    }
                  >
                    Keep local
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      void resolveConflict(conflict.id, "keep_remote")
                    }
                  >
                    Keep remote
                  </button>
                </div>
              </div>
            ))
          )}
        </article>

        <article className="panel">
          <p className="eyebrow">CONNECTED ACCOUNTS</p>
          <form className="sync-form" onSubmit={createConnection}>
            <select name="provider" aria-label="Provider">
              {integrations.map((item) => (
                <option key={item.provider} value={item.provider}>
                  {label(item.provider)}
                </option>
              ))}
            </select>
            <input
              name="account"
              placeholder="Account email or identifier"
              required
            />
            <button className="button" type="submit">
              Prepare connection
            </button>
          </form>
          {accounts.map((account) => (
            <div className="sync-row" key={account.id}>
              <div>
                <strong>{label(account.provider)}</strong>
                <span>{account.display_name}</span>
              </div>
              <em>{account.status}</em>
            </div>
          ))}
        </article>
      </div>

      <section className="panel">
        <p className="eyebrow">INTEGRATIONS</p>
        <div className="integration-grid">
          {integrations.map((item) => (
            <article key={item.provider}>
              <strong>{label(item.provider)}</strong>
              <span>{item.category}</span>
              <p>{item.capabilities.join(" · ")}</p>
              <em>{item.connected ? "Connected" : "Optional"}</em>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <p className="eyebrow">TEAM WORKSPACE</p>
        <form className="sync-form workspace-form" onSubmit={createWorkspace}>
          <input name="name" placeholder="Workspace name" required />
          <input name="description" placeholder="Optional purpose" />
          <button className="button" type="submit">
            Create workspace
          </button>
        </form>
        {workspaces.map((workspace) => (
          <div className="sync-row" key={workspace.id}>
            <div>
              <strong>{workspace.name}</strong>
              <span>{workspace.description || "Private workspace"}</span>
            </div>
            <em>Owner</em>
          </div>
        ))}
      </section>
    </section>
  );
}

function label(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}
