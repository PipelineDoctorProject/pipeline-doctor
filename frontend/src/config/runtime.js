const DEFAULT_API_URL = "http://localhost:8000";

const trimTrailingSlash = (value) => String(value || "").replace(/\/+$/, "");
const toWebSocketUrl = (value) =>
  trimTrailingSlash(value)
    .replace(/^https:\/\//i, "wss://")
    .replace(/^http:\/\//i, "ws://");

export const API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_API_URL || DEFAULT_API_URL
);

export const WS_BASE_URL = toWebSocketUrl(
  import.meta.env.VITE_WS_URL || API_BASE_URL
);

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}
