/**
 * Couche API — fetch avec base configurable.
 *
 * - En dev : VITE_API_BASE = "" (proxy Vite) → appels /api/v1/* same-origin
 * - En prod statique : VITE_API_BASE peut pointer vers le backend directement
 */

const API_BASE =
  import.meta.env.VITE_API_BASE || ""; // "" = proxy, ou URL absolue

export async function apiGet(path) {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status} — ${path}`);
  return r.json();
}

export async function apiPost(path, body) {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} — ${path}`);
  return r.json();
}
