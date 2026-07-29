import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type ApiKey = {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  enabled: boolean;
};
type Webhook = {
  id: string;
  url: string;
  event_types: string[];
  enabled: boolean;
  description: string;
};
type Plugin = {
  id: string;
  name: string;
  version: string;
  plugin_type: string;
  enabled: boolean;
};
type Overview = {
  api_version: string;
  openapi_url: string;
  websocket_url: string;
  api_keys: number;
  webhooks: number;
  plugins: number;
  extension_types: string[];
};

export function DeveloperWorkspace() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [secret, setSecret] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [overviewResponse, keyResponse, webhookResponse, pluginResponse] =
      await Promise.all([
        apiFetch("/api/v1/platform/overview"),
        apiFetch("/api/v1/platform/keys"),
        apiFetch("/api/v1/platform/webhooks"),
        apiFetch("/api/v1/platform/plugins"),
      ]);
    if (overviewResponse.ok) setOverview(await overviewResponse.json());
    if (keyResponse.ok) setKeys(await keyResponse.json());
    if (webhookResponse.ok) setWebhooks(await webhookResponse.json());
    if (pluginResponse.ok) setPlugins(await pluginResponse.json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createKey() {
    const response = await apiFetch("/api/v1/platform/keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: `Developer key ${keys.length + 1}`,
        scopes: ["platform:read", "events:read"],
      }),
    });
    if (!response.ok) return setMessage("Could not create API key.");
    const created = await response.json();
    setSecret(created.secret);
    setMessage("Copy this key now. It is shown only once.");
    await load();
  }

  async function togglePlugin(plugin: Plugin) {
    await apiFetch(`/api/v1/platform/plugins/${plugin.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !plugin.enabled }),
    });
    await load();
  }

  return (
    <section className="review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">PLATFORM</p>
          <h1>Developer Portal</h1>
          <p className="muted">
            Build private integrations against CareerPilot&apos;s versioned API.
          </p>
        </div>
        <a className="button" href="/docs" target="_blank" rel="noreferrer">
          Open API docs
        </a>
      </div>

      <div className="onboarding-grid">
        <article className="panel">
          <strong>{overview?.api_version ?? "v1"}</strong>
          <h2>REST API</h2>
          <code>{overview?.openapi_url ?? "/openapi.json"}</code>
        </article>
        <article className="panel">
          <strong>{overview?.webhooks ?? 0}</strong>
          <h2>Webhooks</h2>
          <p className="muted">Signed event delivery subscriptions.</p>
        </article>
        <article className="panel">
          <strong>{overview?.plugins ?? 0}</strong>
          <h2>Plugins</h2>
          <p className="muted">AI, job-source, and automation extensions.</p>
        </article>
      </div>

      <div className="workspace">
        <article className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">API KEYS</p>
              <h2>Credentials</h2>
            </div>
            <button
              type="button"
              className="button"
              onClick={() => void createKey()}
            >
              Create key
            </button>
          </div>
          {secret && (
            <textarea readOnly value={secret} aria-label="New API key" />
          )}
          {message && <p>{message}</p>}
          {keys.map((key) => (
            <p key={key.id}>
              <strong>{key.name}</strong> <code>{key.prefix}…</code>
            </p>
          ))}
        </article>

        <article className="panel">
          <p className="eyebrow">WEBHOOKS</p>
          <h2>Subscriptions</h2>
          {webhooks.length === 0 ? (
            <p className="empty">No webhook subscriptions configured.</p>
          ) : (
            webhooks.map((webhook) => <p key={webhook.id}>{webhook.url}</p>)
          )}
        </article>
      </div>

      <section className="panel">
        <p className="eyebrow">PLUGIN MANAGEMENT</p>
        <h2>Installed extensions</h2>
        {plugins.length === 0 ? (
          <p className="empty">
            No entry-point plugins discovered. Install a compatible Python
            package to register one.
          </p>
        ) : (
          plugins.map((plugin) => (
            <div className="history-row" key={plugin.id}>
              <strong>{plugin.name}</strong>
              <span>
                {plugin.plugin_type} · {plugin.version}
              </span>
              <button type="button" onClick={() => void togglePlugin(plugin)}>
                {plugin.enabled ? "Disable" : "Enable"}
              </button>
            </div>
          ))
        )}
      </section>
    </section>
  );
}
