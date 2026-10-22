import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmt, pairLabel } from "../data.js";

const PAIR_COLORS = {
  "terra__aqua": "#ff7a33",
  "aqua__viirs_snpp": "#35c8c0",
  "terra__viirs_snpp": "#5aa7ff",
  terra_aqua: "#ff7a33",
  aqua_viirs_snpp: "#35c8c0",
  terra_viirs_snpp: "#5aa7ff",
};

function heatStyle(j) {
  if (j === null || j === undefined) return {};
  const alpha = Math.min(0.55, 0.06 + j * 0.75);
  return { background: `rgba(255, 122, 51, ${alpha})`, fontWeight: 600 };
}

export default function Baselines({ data }) {
  const b = data.baselines;
  const [pair, setPair] = useState(null);
  const [grid, setGrid] = useState(null);
  const [win, setWin] = useState(null);

  const pairs = useMemo(
    () => [...new Set((b?.summary || []).map((r) => r.pair))],
    [b]
  );
  const activePair = pair || pairs[0];
  const grids = b?.grids_deg || [];
  const windows = b?.window_days || [];
  const activeGrid = grid ?? b?.primary?.grid_deg ?? grids[0];
  const activeWin = win ?? b?.primary?.window_days ?? windows[0];

  const monthly = useMemo(() => {
    if (!b) return [];
    const rows = (b.jaccard_monthly || []).filter(
      (r) =>
        r.pair === activePair &&
        Math.abs(r.grid_deg - activeGrid) < 1e-9 &&
        r.window_days === activeWin
    );
    return rows.map((r) => ({ ...r, month: String(r.month).slice(0, 7) }));
  }, [b, activePair, activeGrid, activeWin]);

  // Matrice de sensibilité : jaccard par grille × fenêtre pour la paire active.
  const sensitivity = useMemo(() => {
    if (!b) return [];
    return (b.summary || [])
      .filter((r) => r.pair === activePair)
      .map((r) => ({
        grid: r.grid_deg,
        window: r.window_days,
        jaccard: r.jaccard,
        n_a: r.n_a,
        n_b: r.n_b,
        intersection: r.intersection,
        union: r.union,
      }));
  }, [b, activePair]);

  // Les lignes régionales peuvent porter ou non la configuration ; filtrer si présentes.
  const regions = useMemo(() => {
    if (!b) return [];
    return (b.regions || []).filter((r) => {
      if (r.pair !== activePair) return false;
      if (r.grid_deg === undefined || r.window_days === undefined) return true;
      return Math.abs(r.grid_deg - activeGrid) < 1e-9 && r.window_days === activeWin;
    });
  }, [b, activePair, activeGrid, activeWin]);

  const spatial = useMemo(() => {
    if (!b) return [];
    return (b.spatial || []).filter((r) => {
      if (r.pair !== activePair) return false;
      if (r.grid_deg === undefined || r.window_days === undefined) return true;
      return Math.abs(r.grid_deg - activeGrid) < 1e-9 && r.window_days === activeWin;
    });
  }, [b, activePair, activeGrid, activeWin]);

  if (!b) return <div className="loading">Artefact baselines.json indisponible.</div>;

  return (
    <div>
      <h2 className="page-title">Baselines de concordance</h2>
      <p className="page-sub">
        Comparaisons par clés d'ensembles explicites (cellule de grille × date/fenêtre), jamais
        ligne à ligne. Jaccard = |A ∩ B| / |A ∪ B| calculé par le pipeline ; aucune sélection de
        configuration par maximisation du Jaccard, aucune conversion d'échelle de confiance.
      </p>

      <div className="banner warn">
        <strong>Origine : {b.data_origin}</strong>
        {b.data_origin === "synthetic_fixture"
          ? "Ces concordances sont calculées sur l'échantillon synthétique : elles valident les calculs, elles ne décrivent pas la concordance observée au Cameroun. Les chiffres v0.3 de l'exploratoire ne sont pas recalculés ici."
          : "Toutes les valeurs de cette page sont calculées par le pipeline."}
      </div>

      <div className="panel">
        <h3>
          Définitions des clés d'ensembles
          <span className="hint">identiques pour toutes les configurations</span>
        </h3>
        <ul className="small">
          {Object.entries(b.key_definitions || {}).map(([k, v]) => (
            <li key={k}>
              <span className="mono">{k}</span> — {v}
            </li>
          ))}
        </ul>
        <p className="muted small" style={{ marginBottom: 0 }}>
          Tailles d'ensembles (clés primaires) : Terra {fmt(b.sensor_sizes?.terra)} · Aqua{" "}
          {fmt(b.sensor_sizes?.aqua)} · VIIRS S-NPP {fmt(b.sensor_sizes?.viirs_snpp)}.
        </p>
      </div>

      <div className="panel">
        <h3>
          Résumé par configuration
          <span className="hint">ordre imposé : (A) Terra–Aqua, (B) Aqua–VIIRS, (C) sensibilité</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Paire</th>
                <th>Grille °</th>
                <th>Fenêtre j</th>
                <th>|A|</th>
                <th>|B|</th>
                <th>|A ∩ B|</th>
                <th>|A ∪ B|</th>
                <th>Jaccard</th>
                <th>Clé</th>
              </tr>
            </thead>
            <tbody>
              {(b.summary || []).map((r, i) => (
                <tr key={i}>
                  <td className="txt">
                    <strong>{pairLabel(r.pair)}</strong>
                  </td>
                  <td>{r.grid_deg.toFixed(2)}</td>
                  <td>{r.window_days}</td>
                  <td>{fmt(r.n_a)}</td>
                  <td>{fmt(r.n_b)}</td>
                  <td>{fmt(r.intersection)}</td>
                  <td>{fmt(r.union)}</td>
                  <td style={heatStyle(r.jaccard)}>{r.jaccard === null ? "—" : r.jaccard.toFixed(4)}</td>
                  <td className="muted" style={{ fontSize: 11.5 }}>
                    {r.key_definition}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h3>
          Évolution mensuelle du Jaccard
          <span className="hint">courbes par configuration, calculées</span>
        </h3>
        <div className="controls">
          <label>Paire</label>
          <select value={activePair} onChange={(e) => setPair(e.target.value)}>
            {pairs.map((p) => (
              <option key={p} value={p}>
                {pairLabel(p)}
              </option>
            ))}
          </select>
          <label>Grille</label>
          <select value={activeGrid} onChange={(e) => setGrid(Number(e.target.value))}>
            {grids.map((g) => (
              <option key={g} value={g}>
                {g.toFixed(2)}°
              </option>
            ))}
          </select>
          <label>Fenêtre</label>
          <select value={activeWin} onChange={(e) => setWin(Number(e.target.value))}>
            {windows.map((w) => (
              <option key={w} value={w}>
                {w} j
              </option>
            ))}
          </select>
        </div>

        <div className="chart-box tall">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={monthly} margin={{ left: 10, right: 20, top: 10 }}>
              <CartesianGrid stroke="#23303f" strokeDasharray="3 3" />
              <XAxis dataKey="month" stroke="#8ba0b8" tick={{ fontSize: 11.5 }} />
              <YAxis domain={[0, 1]} stroke="#8ba0b8" tick={{ fontSize: 11.5 }} />
              <Tooltip
                contentStyle={{
                  background: "#131b24",
                  border: "1px solid #23303f",
                  borderRadius: 8,
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="jaccard"
                name={`Jaccard (${activeGrid}° / ${activeWin} j)`}
                stroke={PAIR_COLORS[activePair] || "#ff7a33"}
                strokeWidth={2.4}
                dot={{ r: 3 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="legend-note">
          Jaccard mensuel (0–1) pour la configuration sélectionnée. <span className="pill calc">calculé par le pipeline</span>
          {monthly.length === 0 && " — aucune ligne pour cette configuration."}
        </div>
      </div>

      <div className="panel">
        <h3>
          Sensibilité aux paramètres
          <span className="hint">grilles {grids.join(" / ")}° × fenêtres {windows.join(" / ")} j</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Configuration</th>
                <th>|A|</th>
                <th>|B|</th>
                <th>|A ∩ B|</th>
                <th>|A ∪ B|</th>
                <th>Jaccard</th>
              </tr>
            </thead>
            <tbody>
              {sensitivity
                .sort((x, y) => x.grid - y.grid || x.window - y.window)
                .map((r, i) => (
                  <tr key={i}>
                    <td className="txt">
                      {r.grid.toFixed(2)}° · {r.window} j
                    </td>
                    <td>{fmt(r.n_a)}</td>
                    <td>{fmt(r.n_b)}</td>
                    <td>{fmt(r.intersection)}</td>
                    <td>{fmt(r.union)}</td>
                    <td style={heatStyle(r.jaccard)}>
                      {r.jaccard === null ? "—" : r.jaccard.toFixed(4)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <div className="legend-note">
          Toutes les configurations sont rapportées : aucune n'est retenue parce qu'elle maximise
          le Jaccard.
        </div>
      </div>

      <div className="panel">
        <h3>
          Divergences par région
          <span className="hint">
            paire {pairLabel(activePair)}
            {regions.some((r) => r.grid_deg !== undefined)
              ? ` · configuration ${activeGrid}° / ${activeWin} j`
              : " · agrégées sur la période (sans détail de configuration)"}
          </span>
        </h3>
        {regions.length === 0 ? (
          <p className="muted">Aucune ligne régionale pour cette configuration.</p>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Région</th>
                  <th>Uniquement A</th>
                  <th>Uniquement B</th>
                  <th>Les deux</th>
                  <th>Jaccard local</th>
                </tr>
              </thead>
              <tbody>
                {regions.map((r, i) => {
                  const inter = r.both;
                  const uni = r.a_only + r.b_only + r.both;
                  const j = uni ? inter / uni : null;
                  return (
                    <tr key={i}>
                      <td className="txt">
                        <strong>{r.region}</strong>
                      </td>
                      <td>{fmt(r.a_only)}</td>
                      <td>{fmt(r.b_only)}</td>
                      <td>{fmt(r.both)}</td>
                      <td style={heatStyle(j)}>{j === null ? "—" : j.toFixed(4)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel">
        <h3>
          Distribution spatiale (cellules de grille)
          <span className="hint">désaccord spatial A vs B — configuration primaire</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Cellule (i, j)</th>
                <th>Longitude</th>
                <th>Latitude</th>
                <th>Comptes A</th>
                <th>Comptes B</th>
              </tr>
            </thead>
            <tbody>
              {spatial.slice(0, 30).map((r, i) => (
                <tr key={i}>
                  <td>
                    ({r.cell_i}, {r.cell_j})
                  </td>
                  <td>{Number(r.lon).toFixed(3)}</td>
                  <td>{Number(r.lat).toFixed(3)}</td>
                  <td>{fmt(r.a_count)}</td>
                  <td>{fmt(r.b_count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {spatial.length > 30 && (
          <p className="muted small">
            {spatial.length - 30} cellules supplémentaires dans
            baselines/spatial_distribution.csv.
          </p>
        )}
      </div>
    </div>
  );
}
