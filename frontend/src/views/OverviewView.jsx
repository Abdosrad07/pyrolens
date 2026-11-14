/**
 * OverviewView — vue Aperçu des observations (données mockées du pipeline).
 *
 * Lit les artefacts depuis /public/artifacts/*.json (ou les mocks intégrés).
 */

import { useState, useEffect } from "react";
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

function readArtifact(path, fallback) {
  try {
    const mod = await import(`../../public/artifacts/${path}?t=${Date.now()}`);
    return mod.default || fallback;
  } catch {
    return fallback;
  }
}

export default function OverviewView() {
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

  if (loading) return <div className="content"><p className="empty">Chargement des artefacts du pipeline…</p></div>;

  const { execution } = data;
  const period =
    execution?.period_start && execution?.period_end
      ? `${execution.period_start} → ${execution.period_end}`
      : "—";

  const cards = [
    { k: "Période", v: period, u: "données MODIS/VIIRS" },
    { k: "Satellites", v: data.baselines?.satellites ?? 2, u: "MODIS Terra, Aqua, VIIRS" },
    { k: "Sites pilotes", v: data.baselines?.sites ?? 2, u: "Cameroun, etc." },
    { k: "États observabilité", v: `${data.obs?.states?.green ?? 0} OK`, u: "vert / jaune / orange / rouge" },
    { k: "Pipeline", v: execution?.project_version ?? "—", u: "version" },
  ];

  return (
    <div className="content">
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
          Satellite
          <select defaultValue="VIIRS">
            <option>VIIRS SNPP</option>
            <option>MODIS Terra</option>
            <option>MODIS Aqua</option>
          </select>
        </label>
        <label>
          Date début
          <input type="date" defaultValue={execution?.period_start?.slice(0, 10) || ""} />
        </label>
        <label>
          Date fin
          <input type="date" defaultValue={execution?.period_end?.slice(0, 10) || ""} />
        </label>
      </div>

      <div className="ov-map" style={{ height: "22rem", marginTop: "1rem", borderRadius: "var(--r-m)", overflow: "hidden", boxShadow: "0 0 0 1px var(--mist)" }}>
        <div style={{ height: "100%", background: "#0B2E4A", display: "flex", alignItems: "center", justifyContent: "center", color: "#B9CCC6", fontSize: "0.875rem" }}>
          Carte d&apos;aperçu (voir mode Carte pour la vue interactive)
        </div>
      </div>

      <div className="banner info" style={{ marginTop: "1.2rem" }}>
        <b>Zone couverte :</b> Emprise Cameroun ({CAM_BBOX[1]}°N–{CAM_BBOX[3]}°N, {CAM_BBOX[0]}°E–{CAM_BBOX[2]}°E) · Grille risque {RISK_GRID}°
      </div>
    </div>
  );
}
