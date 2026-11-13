// Chargement des artefacts statiques produits par le pipeline Python.
// Aucun backend : les fichiers sont servis depuis /artifacts (web/public/artifacts).
// Mode API : si VITE_API_BASE est défini, les appels passent par l'API v1.

const BASE = "/artifacts";
// undefined = mode statique ; "" = même origine (proxy Vite /api → backend) ;
// "http://hote:port" = API cross-origin directe (CORS requis côté backend).
const API_BASE = import.meta.env.VITE_API_BASE;
const API_MODE = API_BASE !== undefined;

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
  if (!API_MODE) {
    throw new Error("API mode not enabled (VITE_API_BASE not set)");
  }
  const url = new URL(`${API_BASE ?? ""}/api/v1${path}`, window.location.origin);
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
  if (!API_MODE) {
    throw new Error("API mode not enabled (VITE_API_BASE not set)");
  }
  const url = new URL(`${API_BASE ?? ""}/api/v1${path}`, window.location.origin);
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
  if (API_MODE) {
    const response = await apiGet("/experiments", params);
    // API returns { count, items[] } (JobListView)
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
  if (API_MODE) {
    // ExperimentRequest n'accepte que pair / grid_deg / window_days / source
    // (extra="forbid") : les champs du wizard sans équivalent (ex. dataset) sont retirés.
    const body = {
      pair: data.pair,
      grid_deg: data.grid_deg,
      window_days: data.window_days,
      source: data.source || "auto",
    };
    return apiPost("/experiments", body);
  }
  throw new Error("Experiment creation requires API mode (VITE_API_BASE)");
}

/**
 * Get experiment status by job ID
 * @param {string} jobId - Experiment job ID
 * @returns {Promise<Object>} Experiment status
 */
export async function getExperimentStatus(jobId) {
  if (API_MODE) {
    return apiGet(`/experiments/${jobId}`);
  }
  throw new Error("Experiment tracking requires API mode (VITE_API_BASE)");
}

/**
 * Get experiment results by job ID
 * @param {string} jobId - Experiment job ID
 * @returns {Promise<Object>} Experiment results
 */
/**
 * Get experiment results by job ID.
 * Normalise ExperimentResultResponse ({ job_id, params, result: {...} })
 * vers la forme plate attendue par HarmonizationDetail.
 * @param {string} jobId - Experiment job ID
 * @returns {Promise<Object>} Experiment results
 */
export async function getExperimentResult(jobId) {
  if (API_MODE) {
    const response = await apiGet(`/experiments/${jobId}/result`);
    const inner = response.result || {};
    const src = inner.source || {};
    const monthly = (inner.result?.monthly || []).map((m) => ({
      month: m.month,
      only_a: m.a_only,
      only_b: m.b_only,
      common: m.both,
      jaccard: m.jaccard,
    }));
    const spatialTop = (inner.result?.spatial_top || []).map((c) => ({
      cell_id: `${c.cell_i}:${c.cell_j}`,
      count_a: c.a_count,
      count_b: c.b_count,
      common: null,
    }));
    return {
      job_id: response.job_id,
      params: inner.params || response.params,
      status: response.status,
      data_origin: inner.data_origin,
      generated_at: inner.finished_at,
      started_at: inner.started_at,
      finished_at: inner.finished_at,
      elapsed_s: inner.elapsed_s,
      digest_sha256: src.digest_sha256,
      source: {
        n_files: src.n_files,
        n_rows_total: src.n_rows_loaded,
        n_rows_analyzable:
          (src.n_rows_sensor_a ?? 0) + (src.n_rows_sensor_b ?? 0) || src.n_rows_loaded,
      },
      software: inner.software?.pipeline || inner.software,
      warning: inner.warning,
      result: { ...(inner.result || {}), monthly, spatial_top: spatialTop },
    };
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
  if (API_MODE) {
    const response = await apiGet("/catalog", params);
    // Normalise { datasets: [{ id, kind, period: {start,end}, ... }] }
    // vers la forme attendue par DataCatalog.
    const datasets = (response.datasets || []).map((d) => ({
      ...d,
      type: d.kind === "source" ? "source" : "dérivé",
      period_start: d.period?.start ?? null,
      period_end: d.period?.end ?? null,
      n_records: d.n_records ?? 0,
      n_anomalies: d.n_anomalies ?? 0,
      available: d.available !== false,
    }));
    return { ...response, datasets };
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
  if (API_MODE) {
    const response = await apiGet(`/catalog/${datasetId}`);
    // Normalise { dataset: {...} } vers la forme plate attendue par DatasetDetail.
    const d = response.dataset || response;
    const files = (d.files || []).map((f) => ({
      name: f.file ?? f.name,
      n_records: f.n_records,
      n_anomalies: f.n_anomalies,
      date_min: f.date_min,
      date_max: f.date_max,
    }));
    const sum = (key) => files.reduce((acc, f) => acc + (f[key] || 0), 0);
    return {
      id: d.id,
      label: d.label,
      type: d.kind === "source" ? "source" : "dérivé",
      period_start: d.period?.start ?? files[0]?.date_min ?? null,
      period_end: d.period?.end ?? files[files.length - 1]?.date_max ?? null,
      n_records: d.n_records ?? sum("n_records"),
      n_anomalies: d.n_anomalies ?? sum("n_anomalies"),
      generated_at: response.generated_at ?? d.generated_at,
      data_origin: response.data_origin ?? d.data_origin,
      files,
      artifact: d.artifact,
      available: d.available !== false,
    };
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
  if (API_MODE) {
    const res = await fetch(`${API_BASE ?? ""}/api/v1/methodology`);
    if (!res.ok) throw new Error(`methodology: HTTP ${res.status}`);
    return res.text();
  }
  // Static mode: load from docs/methodology.md
  const res = await fetch("/methodology.md");
  if (!res.ok) throw new Error(`methodology.md: HTTP ${res.status}`);
  return res.text();
}

function rowsToCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const esc = (v) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [headers.join(","), ...rows.map((r) => headers.map((h) => esc(r[h])).join(","))].join("\n");
}

/**
 * Export data.
 * - { job_id, format } : résultat d'expérience (JSON complet ou CSV des
 *   divergences mensuelles), généré côté client depuis /experiments/{id}/result.
 * - { dataset, pair, grid_deg, window_days, format } : export CSV/JSON de
 *   l'API /export (datasets de comparaison publiés).
 * @param {Object} params - Query parameters
 * @returns {Promise<Blob>} File blob for download
 */
export async function exportData(params = {}) {
  if (!API_MODE) {
    throw new Error("Export requires API mode (VITE_API_BASE)");
  }
  const format = params.format || "json";

  if (params.job_id) {
    const result = await getExperimentResult(params.job_id);
    if (format === "csv") {
      const rows = result.result?.monthly?.length
        ? result.result.monthly
        : result.result?.spatial_top || [];
      return new Blob([rowsToCsv(rows)], { type: "text/csv;charset=utf-8" });
    }
    return new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json;charset=utf-8",
    });
  }

  const url = new URL(`${API_BASE ?? ""}/api/v1/export`, window.location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && k !== "format") url.searchParams.set(k, v);
  });
  url.searchParams.set("format", format);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`export: HTTP ${res.status}`);
  return res.blob();
}

// ========== Fire Calendar ==========

/**
 * Charge les séries du calendrier des feux (quotidien, mensuel, Jaccard).
 * API : /fire-calendar/daily + /fire-calendar/monthly. Statique : baselines.json
 * avec la même forme de sortie ({ daily, monthly, jaccard }).
 * @param {Object} params - { pair } ('terra__aqua' | 'aqua__viirs_snpp' | undefined = toutes)
 * @returns {Promise<{generated_at, data_origin, daily, monthly, jaccard}>}
 */
export async function loadFireCalendar({ pair } = {}) {
  if (API_MODE) {
    const [dailyRes, monthlyRes] = await Promise.all([
      apiGet("/fire-calendar/daily", { pair, limit: 20000 }),
      apiGet("/fire-calendar/monthly", { pair, limit: 600 }),
    ]);
    return {
      generated_at: dailyRes.generated_at,
      data_origin: dailyRes.data_origin,
      daily: dailyRes.rows || [],
      monthly: monthlyRes.monthly || [],
      jaccard: monthlyRes.jaccard_monthly || [],
    };
  }
  const baselines = await getJSON("baselines");
  const primary = baselines.primary || {};
  const keepPair = (r) => !pair || r.pair === pair;
  const inPrimary = (r) =>
    r.grid_deg === primary.grid_deg && r.window_days === primary.window_days;
  const withTotal = (r) => ({
    ...r,
    total: (r.a_only || 0) + (r.b_only || 0),
  });
  return {
    generated_at: baselines.generated_at,
    data_origin: baselines.data_origin,
    daily: (baselines.daily || []).filter(keepPair).map(withTotal),
    monthly: (baselines.monthly || []).filter(keepPair).map(withTotal),
    jaccard: (baselines.jaccard_monthly || []).filter(
      (r) => keepPair(r) && inPrimary(r)
    ),
  };
}
