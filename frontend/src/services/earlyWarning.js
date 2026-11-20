/**
 * Service Early Warning Center.
 *
 * Sépare les appels API de la logique UI. Bascule automatique :
 *  - Si le backend expose /api/v1/early-warning/*, on l'utilise.
 *  - Sinon, on retombe sur le fixture statique (mock) et on le signale
 *    via `usingMock` pour afficher l'avertissement « données historiques ».
 *
 * Contrat de données attendu (aligné avec le backend en cours de dev) :
 *
 *  summary:
 *  {
 *    n_cells_monitored: number,
 *    n_anomalies: number,
 *    n_high_priority: number,
 *    n_increasing_zones: number,
 *    data_period: { start: "ISO", end: "ISO", days: number },
 *    historical_backtest: boolean,
 *    data_origin: "nasa_firms" | "synthetic_fixture",
 *    generated_at: "ISO"
 *  }
 *
 *  alerts (list):
 *  {
 *    items: [
 *      {
 *        cell_id: string,        // "i_j" ou index
 *        cell_i: number,
 *        cell_j: number,
 *        lat: number,
 *        lon: number,
 *        severity: "low" | "moderate" | "high" | "critical",
 *        recent_detections: number,
 *        historical_baseline: number,   // médiane historique
 *        activity_change: number,       // % récent vs baseline
 *        persistence: number,           // jours consécutifs
 *        sensors: ["viirs-snpp", "modis"],
 *        observation_period: { start, end },
 *        anomaly_score: number,
 *        reason: string,
 *        limitations: [string]
 *      }
 *    ],
 *    meta: { ...summary fields }
 *  }
 */

import { apiGet } from "./api.js";

const MOCK = {
  enabled: true,
  summary: null,
  alerts: null,
};

// Chargé paresseusement depuis public/early_warning_fixture.json
async function loadFixture() {
  try {
    const r = await fetch("/early_warning_fixture.json");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch {
    return null;
  }
}

export default function useEarlyWarning() {
  return {
    /** GET /api/v1/early-warning/summary — retombe sur le fixture si l'API est absente. */
    async summary() {
      try {
        return await apiGet("/api/v1/early-warning/summary");
      } catch {
        const fix = await loadFixture();
        MOCK.usingMock = true;
        return fix?.summary ?? null;
      }
    },

    /** GET /api/v1/early-warning/alerts — retombe sur le fixture si l'API est absente. */
    async alerts() {
      try {
        return await apiGet("/api/v1/early-warning/alerts");
      } catch {
        const fix = await loadFixture();
        MOCK.usingMock = true;
        return fix?.alerts ?? null;
      }
    },

    /**
     * GET /api/v1/early-warning/alerts/{cell_id}
     * — retombe sur le fixture (recherche dans items) si l'API est absente.
     */
    async alertDetail(cellId) {
      try {
        return await apiGet(`/api/v1/early-warning/alerts/${cellId}`);
      } catch {
        const fix = await loadFixture();
        MOCK.usingMock = true;
        return fix?.alerts?.items?.find((a) => a.cell_id === cellId) ?? null;
      }
    },

    /** true si une des requêtes a utilisé le fixture (pour l'avertissement UI). */
    usingMock() {
      return MOCK.usingMock === true;
    },
  };
}
