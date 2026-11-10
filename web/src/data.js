// Chargement des artefacts statiques produits par le pipeline Python.
// Aucun backend : les fichiers sont servis depuis /artifacts (web/public/artifacts).
// Mode API : si VITE_API_BASE est défini, les appels passent par l'API v1.

const BASE = "/artifacts";
const API_BASE = import.meta.env.VITE_API_BASE || "";

async function getJSON(name) {
  const res = await fetch(`${BASE}/${name}.json`);
  if (!res.ok) throw new Error(`${name}.json: HTTP ${res.status}`);
  return res.json();
}

async function getText(name) {
  const res = await fetch(`${BASE}/${name}.md`);
  if (!res.ok) throw new Error(`${name}.md: HTTP ${res.status}`);
  return res.text();
}

/**
 * API GET request - used when VITE_API_BASE is set
 * @param {string} path - API path (e.g., '/experiments')
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} JSON response
 */
async function apiGet(path, params = {}) {
  if (!API_BASE) {
    throw new Error("API mode not enabled (VITE_API_BASE not set)");
  }
  const url = new URL(`${API_BASE}/api/v1${path}`, window.location.origin);
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v != null) url.searchParams.set(k, v);
  });
  const res = await fetch(url);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: `HTTP ${res.status}` } }));
    throw new Error(error.error?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * API POST request - used for creating experiments
 * @param {string} path - API path (e.g., '/experiments')
 * @param {Object} body - Request body
 * @returns {Promise<Object>} JSON response
 */
async function apiPost(path, body = {}) {
  if (!API_BASE) {
    throw new Error("API mode not enabled (VITE_API_BASE not set)");
  }
  const url = new URL(`${API_BASE}/api/v1${path}`, window.location.origin);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: `HTTP ${res.status}` } }));
    throw new Error(error.error?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Charge tous les artefacts ; un échec isolé ne bloque pas les autres vues. */
export async function loadAll() {
  const jsonNames = [
    "execution",
    "inventory",
    "downloads_summary",
    "audit",
    "baselines",
    "observability",
  ];
  const settled = await Promise.allSettled([
    ...jsonNames.map(getJSON),
    getText("scientific_report"),
  ]);

  const out = { errors: [] };
  jsonNames.forEach((name, i) => {
    const r = settled[i];
    if (r.status === "fulfilled") out[name] = r.value;
    else out.errors.push(String(r.reason));
  });
  const report = settled[jsonNames.length];
  out.report = report.status === "fulfilled" ? report.value : null;
  if (report.status === "rejected") out.errors.push(String(report.reason));
  return out;
}

export const PAIR_LABELS = {
  terra__aqua: "Terra – Aqua (MODIS)",
  aqua__viirs_snpp: "Aqua (MODIS) – VIIRS S-NPP",
  terra__viirs_snpp: "Terra (MODIS) – VIIRS S-NPP",
  terra_aqua: "Terra – Aqua (MODIS)",
  aqua_viirs_snpp: "Aqua (MODIS) – VIIRS S-NPP",
  terra_viirs_snpp: "Terra (MODIS) – VIIRS S-NPP",
};

export const SENSOR_LABELS = {
  terra: "MODIS Terra",
  aqua: "MODIS Aqua",
  viirs_snpp: "VIIRS S-NPP 375 m",
};

export function pairLabel(pair) {
  return PAIR_LABELS[pair] || pair;
}

export function fmt(n, digits = 0) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return Number(n).toLocaleString("fr-FR", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

// ========== API Functions for Harmonization Lab ==========

/**
 * Load experiments list
 * @param {Object} params - Query parameters (status, start_date, end_date, search)
 * @returns {Promise<Object>} Experiments list or static data
 */
export async function loadExperiments(params = {}) {
  if (API_BASE) {
    const response = await apiGet("/experiments", params);
    // API returns { count, items[] } or similar
    return response.items || response;
  }
  // Static mode: experiments don't have artifacts, return empty array
  return [];
}

/**
 * Create a new experiment
 * @param {Object} data - Experiment configuration (pair, grid_deg, window_days, source)
 * @returns {Promise<Object>} Created experiment with job_id
 */
export async function createExperiment(data) {
  if (API_BASE) {
    return apiPost("/experiments", data);
  }
  throw new Error("Experiment creation requires API mode (VITE_API_BASE)");
}

/**
 * Get experiment status by job ID
 * @param {string} jobId - Experiment job ID
 * @returns {Promise<Object>} Experiment status
 */
export async function getExperimentStatus(jobId) {
  if (API_BASE) {
    return apiGet(`/experiments/${jobId}`);
  }
  throw new Error("Experiment tracking requires API mode (VITE_API_BASE)");
}

/**
 * Get experiment results by job ID
 * @param {string} jobId - Experiment job ID
 * @returns {Promise<Object>} Experiment results
 */
export async function getExperimentResult(jobId) {
  if (API_BASE) {
    return apiGet(`/experiments/${jobId}/result`);
  }
  throw new Error("Experiment results require API mode (VITE_API_BASE)");
}

// ========== API Functions for Data & Methodology ==========

/**
 * Load dataset catalog
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Catalog data
 */
export async function loadCatalog(params = {}) {
  if (API_BASE) {
    return apiGet("/catalog", params);
  }
  // Static mode: use inventory.json
  return getJSON("inventory");
}

/**
 * Load dataset details
 * @param {string} datasetId - Dataset identifier
 * @returns {Promise<Object>} Dataset details
 */
export async function loadDatasetDetail(datasetId) {
  if (API_BASE) {
    return apiGet(`/catalog/${datasetId}`);
  }
  // Static mode: try to load from inventory or return null
  const inventory = await getJSON("inventory");
  // Simple lookup - in real implementation would match by ID
  return inventory;
}

/**
 * Load methodology content
 * @returns {Promise<string>} Methodology markdown
 */
export async function loadMethodology() {
  if (API_BASE) {
    const res = await fetch(`${API_BASE}/api/v1/methodology`);
    if (!res.ok) throw new Error(`methodology: HTTP ${res.status}`);
    return res.text();
  }
  // Static mode: load from docs/methodology.md
  const res = await fetch("/methodology.md");
  if (!res.ok) throw new Error(`methodology.md: HTTP ${res.status}`);
  return res.text();
}

/**
 * Export data
 * @param {Object} params - Query parameters (dataset, format, pair, grid_deg, window_days)
 * @returns {Promise<Blob>} File blob for download
 */
export async function exportData(params = {}) {
  if (API_BASE) {
    const url = new URL(`${API_BASE}/api/v1/export`, window.location.origin);
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v != null) url.searchParams.set(k, v);
    });
    const res = await fetch(url);
    if (!res.ok) throw new Error(`export: HTTP ${res.status}`);
    return res.blob();
  }
  throw new Error("Export requires API mode (VITE_API_BASE)");
}
