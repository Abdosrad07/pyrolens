/**
 * Constantes partagées par toute l'application PyroLens.
 *
 * - Design tokens (design system canopy/ash/ember)
 * - Données géographiques (emprise Cameroun)
 * - Paramètres de la couche risque
 * - Données mockées (JOBS, DQ_BASE)
 */

export const RISK_LEVELS = [
  { min: 0.0, label: "Faible", color: "#FFC83D" },
  { min: 0.3, label: "Modéré", color: "#FF8A00" },
  { min: 0.6, label: "Élevé",  color: "#F2541B" },
  { min: 0.8, label: "Critique", color: "#A4201B" },
];

export const RISK_GRID = 0.25; // degrés

export const CAM_BBOX = [8.4, 4.1, 16.4, 13.2]; // [minLon, minLat, maxLon, maxLat]

export const VIEWS = {
  world:   { center: [10, 20],         zoom: 3 },
  africa:  { center: [2, 20],          zoom: 4 },
  wyoming: { center: [41.33, -106.17], zoom: 10 },
  us:      { center: [42, -105],       zoom: 4 },
};

export const GIBS_DATE = new Date(Date.now() - 24 * 3600 * 1000)
  .toISOString()
  .slice(0, 10);

// ---- JOBS ----

export const NOW0 = Date.now();

export const p2 = (n) => String(n).padStart(2, "0");

export const fdt = (ms) => {
  const d = new Date(ms);
  return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()} ${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())}`;
};

export const JOBS = [
  {
    id: 18282,
    name: "frp_timeseries_export",
    user: "fireops",
    state: "PENDING",
    start: null,
    elapsed: 0,
    limit: 60,
    prio: 410,
    exit: "–",
    cmd:
      "sbatch --qos normal --job-name frp_timeseries_export --partition cpu --time 60 --output /dev/null --wrap \"/usr/bin/python3 export_frp.py --cluster 9655\"",
    part: "cpu",
    nodes: "(Resources)",
    gpu: false,
  },
  {
    id: 18281,
    name: "firms_cluster_detect",
    user: "fireops",
    state: "RUNNING",
    start: NOW0 - 259e3,
    elapsed: 259,
    limit: 120,
    prio: 545,
    exit: "SUCCESS (0)",
    cmd:
      "sbatch --qos normal --job-name firms_cluster_detect --partition gpu --time 120 --output /dev/null --wrap \"/usr/bin/python3 detect_clusters.py --sensor VIIRS --days 7\" --gres gpu:h100:4",
    part: "gpu",
    nodes: "gpu1",
    gpu: true,
  },
  {
    id: 18280,
    name: "viirs_hotspot_ingest",
    user: "fireops",
    state: "COMPLETED",
    start: NOW0 - 4 * 3600e3,
    elapsed: 5400,
    limit: 120,
    prio: 520,
    exit: "SUCCESS (0)",
    cmd:
      "sbatch --qos normal --job-name viirs_hotspot_ingest --partition cpu --time 120 --output /dev/null --wrap \"/usr/bin/python3 ingest_firms.py --source VIIRS_SNPP_NRT\"",
    part: "cpu",
    nodes: "cpu3",
    gpu: false,
  },
  {
    id: 18279,
    name: "burned_area_mask",
    user: "gisteam",
    state: "FAILED",
    start: NOW0 - 2 * 3600e3,
    elapsed: 840,
    limit: 90,
    prio: 480,
    exit: "FAILED (1:0)",
    cmd:
      "sbatch --qos low --job-name burned_area_mask --partition gpu --time 90 --output /dev/null --wrap \"/usr/bin/python3 burned_area.py --tile 31UDQ\"",
    part: "gpu",
    nodes: "gpu2",
    gpu: true,
  },
];

// ---- DATA QUALITY ----

export const DQ_CAT = {
  ACQ_DATE: "Temporal",
  ACQ_TIME: "Temporal",
  LATITUDE: "Spatial",
  LONGITUDE: "Spatial",
  COUNTRY: "Spatial",
  FRP: "Measurement",
  BRIGHT_TI4: "Measurement",
  SCAN: "Measurement",
  TRACK: "Measurement",
  CONFIDENCE: "Measurement",
  DAYNIGHT: "Measurement",
  SATELLITE: "Metadata",
  INSTRUMENT: "Metadata",
  VERSION: "Metadata",
  CLUSTER_ID: "Metadata",
};

export const DQ_BASE = [
  [
    "ACQ_DATE",
    "D",
    "Hotspot acquisition date must NOT be greater than current date and must be on or after the sensor start date",
    "Plausibility",
    "All hotspots",
    55,
    ["ALL HOTSPOTS", "VIIRS"],
    2,
  ],
  [
    "LATITUDE",
    "N",
    "Latitude must be a number between -90 and 90 and should never be blank or NULL",
    "Validity",
    "All hotspots",
    36,
    ["ALL HOTSPOTS", "CLUSTERS", "FIRE ALERTS"],
    3,
  ],
  [
    "LONGITUDE",
    "N",
    "Longitude must be a number between -180 and 180 and should never be blank or NULL",
    "Validity",
    "All hotspots",
    19,
    ["ALL HOTSPOTS", "CLUSTERS"],
    3,
  ],
  [
    "FRP",
    "N",
    "Fire radiative power (MW) must be non-negative and should not be missing for VIIRS and MODIS hotspots",
    "Completeness",
    "VIIRS, MODIS",
    "err",
    ["FIRE ALERTS", "VIIRS", "MODIS"],
    2,
  ],
  [
    "CONFIDENCE",
    "A",
    "Confidence must be low, nominal or high (VIIRS) or a value between 0 and 100 (MODIS)",
    "Validity",
    "All hotspots",
    "pass",
    ["ALL HOTSPOTS", "VIIRS", "MODIS"],
    1,
  ],
  [
    "SATELLITE",
    "A",
    "Satellite code must be populated and match a known platform (N, N20, N21, Terra, Aqua)",
    "Consistency",
    "All hotspots",
    "pass",
    ["ALL HOTSPOTS", "MODIS"],
    1,
  ],
  [
    "INSTRUMENT",
    "A",
    "Instrument must be populated and equal to VIIRS or MODIS",
    "Validity",
    "All hotspots",
    "pass",
    ["ALL HOTSPOTS"],
    1,
  ],
  [
    "BRIGHT_TI4",
    "N",
    "Brightness temperature I-4 must be between 200 K and 500 K",
    "Plausibility",
    "VIIRS",
    8,
    ["VIIRS", "FIRE ALERTS"],
    2,
  ],
  [
    "DAYNIGHT",
    "A",
    "Day / night flag must be D or N",
    "Validity",
    "All hotspots",
    "pass",
    ["ALL HOTSPOTS"],
    1,
  ],
  [
    "SCAN",
    "N",
    "Scan size must be positive and must not exceed the sensor swath limit",
    "Plausibility",
    "All hotspots",
    3,
    ["ALL HOTSPOTS", "MODIS"],
    1,
  ],
  [
    "TRACK",
    "N",
    "Track size must be positive and must not exceed the sensor swath limit",
    "Plausibility",
    "All hotspots",
    12,
    ["ALL HOTSPOTS", "VIIRS"],
    2,
  ],
  [
    "ACQ_TIME",
    "D",
    "Acquisition time must be a 4-digit HHMM value between 0000 and 2359",
    "Validity",
    "All hotspots",
    "err",
    ["ALL HOTSPOTS", "FIRE ALERTS"],
    2,
  ],
  [
    "VERSION",
    "A",
    "Product version must be populated for every hotspot",
    "Completeness",
    "All hotspots",
    "pass",
    ["ALL HOTSPOTS"],
    1,
  ],
  [
    "CLUSTER_ID",
    "A",
    "Cluster ID must not be missing for hotspots attached to a fire event",
    "Completeness",
    "Clusters",
    23,
    ["CLUSTERS", "FIRE ALERTS"],
    3,
  ],
  [
    "COUNTRY",
    "A",
    "Country code should be populated for hotspots located on land",
    "Completeness",
    "All hotspots",
    "none",
    ["ALL HOTSPOTS"],
    1,
  ],
  [
    "CLUSTER_ID",
    "A",
    "Cluster ID must be unique across cluster polygons",
    "Uniqueness",
    "Clusters",
    "pass",
    ["CLUSTERS"],
    1,
  ],
];

export function buildDQRules() {
  const p2 = (n) => String(n).padStart(2, "0");
  const rules = [];
  for (let p = 0; p < 3; p++) {
    DQ_BASE.forEach((r, i) => {
      let status = r[5];
      if (typeof status === "number")
        status = Math.max(1, Math.min(96, status + p * 4 - 4 + (i % 3)));
      rules.push({
        id: `FIR-${p2(p * 16 + i + 1)}`,
        col: r[0],
        ty: r[1],
        txt: r[2],
        dim: r[3],
        scope: r[4],
        status,
        ents: r[6],
        sev: r[7],
        cat: DQ_CAT[r[0]],
      });
    });
  }
  return rules;
}
