const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8005";

function buildUrl(path: string, params?: Record<string, string | number | undefined>) {
  const u = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") u.searchParams.set(k, String(v));
    });
  }
  return u.toString();
}

export async function getJson(path: string, params?: Record<string, string | number | undefined>) {
  const response = await fetch(buildUrl(path, params));
  if (!response.ok) throw new Error(`API error ${response.status} on ${path}`);
  return response.json();
}

export async function getGeoJson(path: string) {
  return getJson(path);
}
