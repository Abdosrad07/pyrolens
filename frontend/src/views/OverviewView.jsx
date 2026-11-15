/**
 * OverviewView — vue Aperçu des observations (données mockées du pipeline).
 *
 * Lit les artefacts depuis /public/artifacts/*.json (ou les mocks intégrés).
 */

import { useState, useEffect } from "react";
import MapView from "../components/MapView.jsx";
import { CAM_BBOX, RISK_GRID } from "../data/constants.js";

const MOCK_EXECUTION = {
  period_start: "2025-01-01",
  period_end: "2025-12-31",
  project_version: "v0.3.0",
  generated_at: "2025-11-14T08:30:00Z",
};

const MOCK_BASELINES = {
  generated_at: "2025-11-14T08:30:00Z",
  sites: 2,
  satellites: 2,
};

const MOCK_AUDIT = {
  generated_at: "2025-11-14T08:30:00Z",
};

const MOCK_OBS = {
  states: { green: 12, yellow: 3, orange: 1, red: 0 },
};

async function readArtifact(path, fallback) {
  try {
    const r = await fetch(`/artifacts/${path}?t=${Date.now()}`);
    if (!r.ok) return fallback;
    return await r.json();
  } catch {
    return fallback;
  }
}

import { useI18n } from "../i18n/index.jsx";

export default function OverviewView({ onBack }) {
  const { t } = useI18n();
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    async function load() {
      const [execution, audit, baselines, obs] = await Promise.all([
        readArtifact("execution.json", MOCK_EXECUTION),
        readArtifact("audit.json", MOCK_AUDIT),
        readArtifact("baselines.json", MOCK_BASELINES),
        readArtifact("observability.json", MOCK_OBS),
      ]);
      if (alive) setData({ execution, audit, baselines, obs });
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, []);

  if (loading) return <div className="content"><p className="empty">{t("overview.loading", "Chargement des artefacts du pipeline…")}</p></div>;

  const { execution } = data;
  const period =
    execution?.period_start && execution?.period_end
      ? `${execution.period_start} → ${execution.period_end}`
      : "—";

  const cards = [
    { k: t("overview.cards.period", "Période"), v: period, u: t("overview.cards.unitPeriod") },
    { k: t("overview.cards.satellites", "Satellites"), v: data.baselines?.satellites ?? 2, u: t("overview.cards.unitSatellites") },
    { k: t("overview.cards.pilotSites", "Sites pilotes"), v: data.baselines?.sites ?? 2, u: t("overview.cards.unitSites") },
    { k: t("overview.cards.obsStates", "États observabilité"), v: `${data.obs?.states?.green ?? 0} OK`, u: t("overview.cards.unitObs") },
    { k: t("overview.cards.pipeline", "Pipeline"), v: execution?.project_version ?? "—", u: t("overview.cards.unitPipeline") },
  ];

  return (
    <div className="content">
      {onBack && (
        <button className="btn-back" type="button" onClick={onBack} style={{ marginBottom: "0.8rem" }}>
          ← Retour à la carte
        </button>
      )}
      <h2>Aperçu des observations</h2>
      <small>
        Résumé synthétique du pipeline de traitement. Données mockées si les artefacts
        publics ne sont pas disponibles.
      </small>
      <div className="cards">
        {cards.map((c, i) => (
          <div key={i} className="card">
            <div className="k">{c.k}</div>
            <div className="v">{c.v}</div>
            <div className="u">{c.u}</div>
          </div>
        ))}
      </div>

      <div className="controls" style={{ marginTop: "1.5rem" }}>
        <label>
          {t("overview.satellite", "Satellite")}
          <select defaultValue="VIIRS">
            <option>{t("overview.satellitesOpt.viirs", "VIIRS SNPP")}</option>
            <option>{t("overview.satellitesOpt.terra", "MODIS Terra")}</option>
            <option>{t("overview.satellitesOpt.aqua", "MODIS Aqua")}</option>
          </select>
        </label>
        <label>
          {t("overview.startDate", "Date début")}
          <input type="date" defaultValue={execution?.period_start?.slice(0, 10) || ""} />
        </label>
        <label>
          {t("overview.endDate", "Date fin")}
          <input type="date" defaultValue={execution?.period_end?.slice(0, 10) || ""} />
        </label>
      </div>

      <div className="ov-map" style={{ height: "22rem", marginTop: "1rem", borderRadius: "var(--r-m)", overflow: "hidden", boxShadow: "0 0 0 1px var(--mist)", position: "relative" }}>
        <MapView
          activeBase="esri"
          showRisk={false}
          riskThreshold={0}
          riskData={null}
        />
      </div>

      <div className="banner info" style={{ marginTop: "1.2rem" }}>
        <b>{t("overview.zoneCovered", "Zone couverte :")}</b> Emprise Cameroun ({CAM_BBOX[1]}°N–{CAM_BBOX[3]}°N, {CAM_BBOX[0]}°E–{CAM_BBOX[2]}°E) · {t("overview.gridRisk", "Grille risque")} {RISK_GRID}°
      </div>
    </div>
  );
}
