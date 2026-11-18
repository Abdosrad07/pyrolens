/**
 * HarmonizationLabView — vue "Harmonisation Lab".
 *
 * Affiche les graphes de recouvrement inter-capteurs (Jaccard) entre
 * VIIRS et MODIS, ainsi que le graphe de leur harmonisation sur la
 * grille commune 0,25°.
 *
 * Données : /api/v1/baselines/series/jaccard?pair=...
 *          /api/v1/baselines/summary
 *
 * Props: { onBack: () => void }
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { apiGet } from "../services/api.js";
import { useI18n } from "../i18n/index.jsx";

const PAIRS = [
  { id: "aqua__viirs_snpp", label: "Aqua ↔ VIIRS", fr: "Aqua ↔ VIIRS" },
  { id: "terra__aqua", label: "Terra ↔ Aqua", fr: "Terra ↔ Aqua" },
];

const GRIDS = [0.1, 0.25, 0.5];
const WINDOWS = [1, 4, 8, 16];

/**
 * Graphe SVG simple de la série mensuelle Jaccard.
 * Reçoit : rows = [{ month: "2019-01", jaccard: 0.335, both: 120, a_only: 45, b_only: 30 }, ...]
 */
function JaccardChart({ rows, title, height = 280 }) {
  if (!rows?.length) {
    return <div style={{ padding: "1rem", opacity: 0.5, textAlign: "center" }}>Pas de données</div>;
  }

  const W = 700;
  const H = height;
  const pad = { top: 20, right: 20, bottom: 40, left: 50 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  const maxY = Math.max(...rows.map((r) => r.jaccard || 0), 0.01);
  const n = rows.length;

  const x = (i) => pad.left + (i / Math.max(n - 1, 1)) * plotW;
  const y = (v) => pad.top + plotH - (v / maxY) * plotH;

  // Ligne principale
  const line = rows.map((r, i) => `${i ? "L" : "M"}${x(i)},${y(r.jaccard || 0)}`).join(" ");
  // Zone sous la ligne
  const area = `${line} L${x(n - 1)},${pad.top + plotH} L${x(0)},${pad.top + plotH} Z`;

  return (
    <div style={{ width: "100%", overflow: "auto" }}>
      <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem", opacity: 0.8 }}>{title}</h4>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: H, background: "rgba(0,0,0,0.15)", borderRadius: "0.5rem" }}>
        {/* Grille Y */}
        {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
          const yy = y(tick * maxY);
          return (
            <g key={tick}>
              <line x1={pad.left} y1={yy} x2={W - pad.right} y2={yy} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
              <text x={pad.left - 8} y={yy + 4} textAnchor="end" fontSize={10} fill="rgba(255,255,255,0.4)">
                {(tick * maxY).toFixed(2)}
              </text>
            </g>
          );
        })}
        {/* Zone + ligne */}
        <path d={area} fill="rgba(240,130,50,0.15)" />
        <path d={line} fill="none" stroke="#f08232" strokeWidth={2.5} strokeLinejoin="round" />
        {/* Points */}
        {rows.map((r, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(r.jaccard || 0)} r={3} fill="#f08232" />
            {i % Math.max(1, Math.floor(n / 10)) === 0 && (
              <text x={x(i)} y={H - 8} textAnchor="middle" fontSize={9} fill="rgba(255,255,255,0.5)">
                {r.month?.slice(0, 7) || r.label || ""}
              </text>
            )}
          </g>
        ))}
        {/* Titre Y */}
        <text x={12} y={H / 2} transform={`rotate(-90 12 ${H / 2})`} textAnchor="middle" fontSize={10} fill="rgba(255,255,255,0.5)">
          Jaccard
        </text>
      </svg>
    </div>
  );
}

/**
 * Carte de chaleur de la distribution spatiale (cellules avec a_count, b_count).
 */
function SpatialHeatmap({ rows, width = 700, height = 200 }) {
  if (!rows?.length) return null;
  const maxV = Math.max(...rows.map((r) => (r.a_count || 0) + (r.b_count || 0)), 1);

  return (
    <div>
      <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem", opacity: 0.8 }}>
        Distribution spatiale — top {Math.min(rows.length, 50)} cellules
      </h4>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(10, 1fr)",
        gap: "2px",
        width: "100%",
        maxWidth: width,
      }}>
        {rows.slice(0, 50).map((r, i) => {
          const v = ((r.a_count || 0) + (r.b_count || 0)) / maxV;
          const color = v > 0.7 ? "#f08232" : v > 0.4 ? "#f5a962" : v > 0.2 ? "#f8c98a" : "rgba(255,255,255,0.08)";
          return (
            <div
              key={i}
              title={`cellule (${r.cell_i}, ${r.cell_j}) — A:${r.a_count || 0}, B:${r.b_count || 0}`}
              style={{
                height: 18,
                background: color,
                borderRadius: 2,
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            />
          );
        })}
      </div>
      <small style={{ opacity: 0.5, fontSize: "0.7rem", marginTop: "0.3rem", display: "block" }}>
        Intensité = (détections A + B) / max. Survoler pour les détails.
      </small>
    </div>
  );
}

export default function HarmonizationLabView({ onBack }) {
  const { t } = useI18n();
  const [pair, setPair] = useState("aqua__viirs_snpp");
  const [grid, setGrid] = useState(0.25);
  const [window, setWindow] = useState(8);
  const [summary, setSummary] = useState(null);
  const [series, setSeries] = useState(null);
  const [spatial, setSpatial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, j, sp] = await Promise.all([
        apiGet(`/api/v1/baselines/summary?pair=${pair}&grid_deg=${grid}&window_days=${window}`),
        apiGet(`/api/v1/baselines/series/jaccard?pair=${pair}&grid_deg=${grid}&window_days=${window}`),
        apiGet(`/api/v1/baselines/spatial?pair=${pair}&grid_deg=${grid}&window_days=${window}&limit=50`),
      ]);
      setSummary(s?.rows?.[0] || null);
      setSeries(j?.rows || []);
      setSpatial(sp?.rows || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [pair, grid, window]);

  useEffect(() => { load(); }, [load]);

  const jaccardPct = summary?.jaccard != null ? `${(summary.jaccard * 100).toFixed(1)}%` : "—";

  return (
    <div className="content" style={{ overflowY: "auto", padding: "1.2rem" }}>
      <button className="btn-back" type="button" onClick={onBack} style={{ marginBottom: "0.8rem" }}>
        {t("common.backToMap", "← Retour à la carte")}
      </button>

      <h2 style={{ margin: "0 0 0.3rem" }}>Harmonisation Lab</h2>
      <small style={{ opacity: 0.6, display: "block", marginBottom: "1rem" }}>
        Recouvrement inter-capteurs (Jaccard) et harmonisation sur grille commune.
      </small>

      {/* Contrôles */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.8rem", marginBottom: "1rem" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
          Paire
          <select value={pair} onChange={(e) => setPair(e.target.value)} style={{
            background: "rgba(255,255,255,0.08)", color: "#fff", border: "none", borderRadius: "0.4rem",
            padding: "0.4rem 0.6rem", fontSize: "0.85rem",
          }}>
            {PAIRS.map((p) => <option key={p.id} value={p.id} style={{ background: "#0e2e29" }}>{p.fr}</option>)}
          </select>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
          Grille
          <select value={grid} onChange={(e) => setGrid(parseFloat(e.target.value))} style={{
            background: "rgba(255,255,255,0.08)", color: "#fff", border: "none", borderRadius: "0.4rem",
            padding: "0.4rem 0.6rem", fontSize: "0.85rem",
          }}>
            {GRIDS.map((g) => <option key={g} value={g} style={{ background: "#0e2e29" }}>{g}°</option>)}
          </select>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
          Fenêtre
          <select value={window} onChange={(e) => setWindow(parseInt(e.target.value))} style={{
            background: "rgba(255,255,255,0.08)", color: "#fff", border: "none", borderRadius: "0.4rem",
            padding: "0.4rem 0.6rem", fontSize: "0.85rem",
          }}>
            {WINDOWS.map((w) => <option key={w} value={w} style={{ background: "#0e2e29" }}>{w} j</option>)}
          </select>
        </label>
      </div>

      {loading && <p style={{ opacity: 0.5 }}>Chargement des artefacts…</p>}
      {error && <div className="banner err" style={{ marginBottom: "1rem" }}>{error}</div>}

      {/* KPI */}
      {!loading && !error && summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "0.8rem", marginBottom: "1.2rem" }}>
          <div style={{ padding: "0.8rem", background: "rgba(255,255,255,0.04)", borderRadius: "0.5rem" }}>
            <div style={{ fontSize: "0.7rem", opacity: 0.5, marginBottom: "0.2rem" }}>JACCARD</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#f08232" }}>{jaccardPct}</div>
          </div>
          <div style={{ padding: "0.8rem", background: "rgba(255,255,255,0.04)", borderRadius: "0.5rem" }}>
            <div style={{ fontSize: "0.7rem", opacity: 0.5, marginBottom: "0.2rem" }}>DÉTECTIONS A</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{summary.a_size ?? "—"}</div>
          </div>
          <div style={{ padding: "0.8rem", background: "rgba(255,255,255,0.04)", borderRadius: "0.5rem" }}>
            <div style={{ fontSize: "0.7rem", opacity: 0.5, marginBottom: "0.2rem" }}>DÉTECTIONS B</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{summary.b_size ?? "—"}</div>
          </div>
          <div style={{ padding: "0.8rem", background: "rgba(255,255,255,0.04)", borderRadius: "0.5rem" }}>
            <div style={{ fontSize: "0.7rem", opacity: 0.5, marginBottom: "0.2rem" }}>INTERSECTION</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{summary.intersection ?? "—"}</div>
          </div>
        </div>
      )}

      {/* Graphes */}
      {!loading && series && series.length > 0 && (
        <div style={{ marginBottom: "1.2rem" }}>
          <JaccardChart
            rows={series}
            title={`Série mensuelle Jaccard — ${pair.replace("__", " ↔ ")} (${grid}°, ${window} j)`}
          />
        </div>
      )}

      {!loading && spatial && spatial.length > 0 && (
        <div style={{ marginBottom: "1.2rem" }}>
          <SpatialHeatmap rows={spatial} />
        </div>
      )}

      {/* Note méthodologique */}
      <div style={{
        marginTop: "1rem",
        padding: "0.8rem",
        background: "rgba(240,130,50,0.06)",
        borderLeft: "3px solid #f08232",
        borderRadius: "0 0.4rem 0.4rem 0",
        fontSize: "0.8rem",
        opacity: 0.85,
      }}>
        <strong>Note méthodologique :</strong> Le Jaccard mesure le recouvrement
        d'ensembles de cellules (cellule × date), pas la précision. Il ne doit
        pas être interprété comme une « fiabilité des détections ». Une référence
        indépendante n'est pas mobilisée (H4/H6 non exécutés).
      </div>
    </div>
  );
}
