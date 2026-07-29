import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import {
  API_BASE_URL,
  apiFetch,
  clearAccessToken,
  getAccessToken,
  installAuthenticatedFetch,
  setAccessToken,
} from "./api";

type AuthState = "checking" | "local" | "authenticated" | "required";

export function AuthGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>("checking");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/diagnostics`)
      .then(async (response) => {
        if (!response.ok) throw new Error("CareerPilot API is unavailable.");
        const diagnostics = (await response.json()) as {
          authentication: boolean;
        };
        if (!diagnostics.authentication) {
          setState("local");
          return;
        }
        if (!getAccessToken()) {
          setState("required");
          return;
        }
        const me = await apiFetch("/api/v1/auth/me");
        if (me.ok) {
          installAuthenticatedFetch();
          setState("authenticated");
        } else {
          clearAccessToken();
          setState("required");
        }
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: data.get("email"),
        password: data.get("password"),
      }),
    });
    const body = (await response.json()) as {
      access_token?: string;
      detail?: string;
    };
    if (!response.ok || !body.access_token) {
      setError(body.detail ?? "Authentication failed.");
      return;
    }
    setAccessToken(body.access_token);
    installAuthenticatedFetch();
    setState("authenticated");
  }

  if (state === "local" || state === "authenticated") return children;

  if (state === "checking" && !error) {
    return <main className="auth-shell">Checking CareerPilot security…</main>;
  }

  return (
    <main className="auth-shell">
      <form
        className="auth-card"
        onSubmit={(event) => void authenticate(event)}
      >
        <p className="eyebrow">CAREERPILOT SECURITY</p>
        <h1>{mode === "login" ? "Sign in" : "Create the owner account"}</h1>
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
            minLength={12}
            required
          />
        </label>
        {error && <p className="warning-text">{error}</p>}
        <button className="button" type="submit">
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
        <button
          type="button"
          onClick={() => {
            setError("");
            setMode(mode === "login" ? "register" : "login");
          }}
        >
          {mode === "login"
            ? "First run? Create owner account"
            : "Use existing account"}
        </button>
      </form>
    </main>
  );
}
