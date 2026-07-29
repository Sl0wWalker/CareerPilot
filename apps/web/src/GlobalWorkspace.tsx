import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function GlobalWorkspace() {
  const [locale, setLocale] = useState(navigator.language || "en-US");
  const [region, setRegion] = useState("US");
  const [currency, setCurrency] = useState("USD");
  const [saved, setSaved] = useState("");
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  async function save() {
    const response = await fetch(`${API}/api/v1/global/preferences`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        locale,
        region,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        currency,
        measurement_system: region === "US" ? "imperial" : "metric",
        reduced_motion: window.matchMedia("(prefers-reduced-motion: reduce)")
          .matches,
        high_contrast: window.matchMedia("(prefers-contrast: more)").matches,
        regional_job_rules: {},
      }),
    });
    setSaved(
      response.ok
        ? "Preferences saved locally."
        : "Unable to save preferences.",
    );
  }

  return (
    <section className="review" aria-labelledby="global-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">GLOBAL & MOBILE</p>
          <h1 id="global-title">Your market, language, and device</h1>
        </div>
        <span className={`status status-${online ? "online" : "offline"}`}>
          {online ? "Online" : "Offline mode"}
        </span>
      </div>
      <div className="onboarding-grid">
        <article className="panel">
          <h2>Regional experience</h2>
          <label>
            Language
            <select
              value={locale}
              onChange={(event) => setLocale(event.target.value)}
            >
              <option value="en-US">English (United States)</option>
              <option value="en-GB">English (United Kingdom)</option>
              <option value="es-MX">Español (México)</option>
              <option value="fr-FR">Français (France)</option>
              <option value="de-DE">Deutsch (Deutschland)</option>
              <option value="hi-IN">हिन्दी (भारत)</option>
            </select>
          </label>
          <label>
            Job market
            <select
              value={region}
              onChange={(event) => setRegion(event.target.value)}
            >
              <option value="US">United States</option>
              <option value="CA">Canada</option>
              <option value="GB">United Kingdom</option>
              <option value="IN">India</option>
              <option value="DE">Germany</option>
              <option value="AU">Australia</option>
            </select>
          </label>
          <label>
            Currency
            <input
              value={currency}
              maxLength={3}
              onChange={(event) =>
                setCurrency(event.target.value.toUpperCase())
              }
            />
          </label>
          <button type="button" className="button" onClick={() => void save()}>
            Save preferences
          </button>
          <p aria-live="polite">{saved}</p>
        </article>
        <article className="panel">
          <h2>Installable mobile experience</h2>
          <p className="muted">
            CareerPilot is now installable as a progressive web app. The app
            shell remains available offline; sensitive API data is never placed
            in the service-worker cache.
          </p>
          <ul>
            <li>Responsive touch-first layout</li>
            <li>Offline shell and reconnect awareness</li>
            <li>Device endpoint foundation for supervised notifications</li>
            <li>Reduced-motion and high-contrast preferences</li>
          </ul>
        </article>
        <article className="panel">
          <h2>Privacy-aware AI routing</h2>
          <p className="muted">
            Each task can prefer on-device Ollama, set a privacy class, and
            explicitly permit or forbid cloud fallback. Restricted data stays
            local by default.
          </p>
        </article>
      </div>
    </section>
  );
}
