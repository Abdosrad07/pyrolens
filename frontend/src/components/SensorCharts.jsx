/**
 * SensorCharts — courbes de fonctionnement des capteurs MODIS/VIIRS.
 *
 * Sert en fin de DqView : 2 courbes mensuelles (Jaccard + divergence)
 * issues des artefacts baselines (données réelles du pipeline).
 */

import { useState, useEffect, useCallback } from "react";
import { apiGet } from "../services/api.js";
import { useI18n } from "../i18n/index.jsx";

const PAIRS = [
  { id: "aqua__viirs_snpp", label: "Aqua ↔ VIIRS" },
  { id: "terra__aqua", label: "Terra ↔ Aqua" },
];

/** Graphe SVG simple — ligne + zone, avec axes. */
function SensorLineChart({ rows, xKey, yKey, title, color, height = 220, yLabel = "", yFormat = (v) => v }) {
  if (!rows?.length) {
    return (
      <div style={{ padding: "1rem", opacity: 0.5, textAlign: "center", fontSize: "0.85rem" }}>
        Pas de données pour « {title} »
      </div>
    );
  }

  const W = 720;
  const H = height;
  const pad = { top: 20, right: 20, bottom: 40, left: 60 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  const values = rows.map((r) => Number(r[yKey]) || 0);
  const maxY = Math.max(...values, 0.01);
  const n = rows.length;

  const x = (i) => pad.left + (i / Math.max(n - 1, 1)) * plotW;
  const y = (v) => pad.top + plotH - (v / maxY) * plotH;

  const line = rows.map((r, i) => `${i ? "L" : "M"}${x(i)},${y(Number(r[yKey]) || 0)}`).join(" ");
  const area = `${line} L${x(n - 1)},${pad.top + plotH} L${x(0)},${pad.top + plotH} Z`;

  // Ticks Y (5 valeurs)
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({ v: f * maxY, yy: y(f * maxY) }));
  // Ticks X (au plus 6 labels)
  const xStep = Math.max(1, Math.floor(n / 6));

  return (
    <div>
      <h4 style={{ margin: "0 0 0.4rem", fontSize: "0.88rem", opacity: 0.85 }}>{title}</h4>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: H, background: "rgba(0,0,0,0.12)", borderRadius: "0.5rem" }}>
        {/* Grille Y */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={pad.left} y1={t.yy} x2={W - pad.right} y2={t.yy} stroke="rgba(255,255,255,0.07)" strokeWidth={1} />
            <text x={pad.left - 8} y={t.yy + 4} textAnchor="end" fontSize={10} fill="rgba(255,255,255,0.4)">
              {yFormat(t.v)}
            </text>
          </g>
        ))}
        {/* Zone */}
        <path d={area} fill={color} fillOpacity={0.12} />
        {/* Ligne */}
        <path d={line} fill="none" stroke={color} strokeWidth={2.5} strokeLinejoin="round" />
        {/* Points + labels X */}
        {rows.map((r, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(Number(r[yKey]) || 0)} r={3} fill={color}>
              <title>{`${r[xKey] || r.label || ""} : ${yFormat(Number(r[yKey]) || 0)}`}</title>
            </circle>
            {i % xStep === 0 && (
              <text x={x(i)} y={H - 8} textAnchor="middle" fontSize={9} fill="rgba(255,255,255,0.5)">
                {String(r[xKey] || r.label || "").slice(0, 7)}
              </text>
            )}
          </g>
        ))}
        {/* Titre Y */}
        {yLabel && (
          <text x={14} y={H / 2} transform={`rotate(-90 14 ${H / 2})`} textAnchor="middle" fontSize={10} fill="rgba(255,255,255,0.5)">
            {yLabel}
          </text>
        )}
      </svg>
    </div>
  );
}

export default function SensorCharts() {
  const { t } = useI18n();
  const [pair, setPair] = useState("aqua__viirs_snpp");
  const [jaccard, setJaccard] = useState(null);
  const [divergence, setDivergence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Une seule source : jaccard_monthly porte jaccard + a_only + b_only + both.
      // La divergence = a_only + b_only (cellules d'un capteur seulement).
      const j = await apiGet(`/api/v1/baselines/series/jaccard?pair=${pair}&grid_deg=0.25&window_days=8`);
      const rows = j?.rows || [];
      setJaccard(rows);
      setDivergence(rows.map((r) => ({ ...r, divergence: (Number(r.a_only) || 0) + (Number(r.b_only) || 0) })));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [pair]);

  useEffect(() => { load(); }, [load]);

  const VIIRS = "#f08232"; // orange
  const MODIS = "#4ecdc4"; // turquoise

  return (
    <div style={{ marginTop: "1.4rem", paddingTop: "1rem", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.6rem" }}>
        <h4 style={{ margin: 0, fontSize: "0.95rem" }}>
          {t("dq.sensorCharts", "Fonctionnement des capteurs MODIS / VIIRS")}
        </h4>
        <select
          value={pair}
          onChange={(e) => setPair(e.target.value)}
          style={{
            background: "rgba(255,255,255,0.08)",
            color: "#fff",
            border: "none",
            borderRadius: "0.4rem",
            padding: "0.3rem 0.5rem",
            fontSize: "0.8rem",
          }}
        >
          {PAIRS.map((p) => <option key={p.id} value={p.id} style={{ background: "#0e2e29" }}>{p.label}</option>)}
        </select>
      </div>

      <small style={{ opacity: 0.55, fontSize: "0.75rem", display: "block", marginBottom: "0.8rem" }}>
        {t("dq.sensorChartsSub", "Séries mensuelles issues des artefacts du pipeline (grille 0,25° · fenêtre 8 j).")}
      </small>

      {loading && <p style={{ opacity: 0.5, margin: "0.5rem 0" }}>Chargement des séries capteurs…</p>}
      {error && <div className="banner err" style={{ marginBottom: "0.8rem" }}>{t("dq.sensorChartsErr", "Séries capteurs indisponibles :")} {error}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
        <SensorLineChart
          rows={jaccard}
          xKey="month"
          yKey="jaccard"
          title={`${t("dq.jaccard", "Recouvrement Jaccard")} — ${pair.replace("__", " ↔ ")}`}
          color={VIIRS}
          yLabel={t("dq.jaccard", "Jaccard")}
          yFormat={(v) => (v * 100).toFixed(0) + "%"}
        />
        <SensorLineChart
          rows={divergence}
          xKey="month"
          yKey="divergence"
          title={`${t("dq.divergence", "Divergence inter-capteurs")} — ${pair.replace("__", " ↔ ")}`}
          color={MODIS}
          yLabel={t("dq.divergence", "Divergence")}
          yFormat={(v) => String(v)}
        />
      </div>

      <div style={{ marginTop: "0.8rem", display: "flex", gap: "1rem", fontSize: "0.75rem", opacity: 0.7 }}>
        <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ width: 10, height: 10, borderRadius: 3, background: VIIRS, display: "inline-block" }} />
          VIIRS SNPP
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ width: 10, height: 10, borderRadius: 3, background: MODIS, display: "inline-block" }} />
          MODIS Terra/Aqua
        </span>
      </div>
    </div>
  );
}
