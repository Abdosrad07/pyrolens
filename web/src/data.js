// Chargement des artefacts statiques produits par le pipeline Python.
// Aucun backend : les fichiers sont servis depuis /artifacts (web/public/artifacts).

const BASE = "/artifacts";

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
