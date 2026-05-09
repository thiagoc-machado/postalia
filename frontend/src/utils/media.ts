const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function getApiOrigin() {
  try {
    const parsed = new URL(API_BASE_URL, window.location.origin);
    const path = parsed.pathname.replace(/\/?api\/?$/, "");
    return `${parsed.origin}${path}`.replace(/\/$/, "");
  } catch {
    return "";
  }
}

export function resolveMediaUrl(value?: string | null) {
  const candidate = (value || "").trim();
  if (!candidate) return "";
  if (/^https?:\/\//i.test(candidate) || candidate.startsWith("data:")) return candidate;
  if (candidate.startsWith("/")) {
    const origin = getApiOrigin();
    return origin ? `${origin}${candidate}` : candidate;
  }
  const origin = getApiOrigin();
  if (!origin) return candidate;
  return `${origin}/${candidate.replace(/^\/+/, "")}`;
}
