export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "careerpilot.access_token";
const nativeFetch = window.fetch.bind(window);
let authenticatedFetchInstalled = false;

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  return nativeFetch(url, { ...init, headers });
}

export function installAuthenticatedFetch(): void {
  if (authenticatedFetchInstalled) return;
  window.fetch = (input: RequestInfo | URL, init: RequestInit = {}) => {
    const headers = new Headers(
      init.headers ?? (input instanceof Request ? input.headers : undefined),
    );
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return nativeFetch(input, { ...init, headers });
  };
  authenticatedFetchInstalled = true;
}
