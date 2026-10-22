import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmt, SENSOR_LABELS } from "../data.js";

const STATES = [
  { key: "detection_observed", color: "#ff7a33" },
  { key: "no_detection_plausible_conditions", color: "#35c8c0" },
  { key: "unknown_observability", color: "#8ba0b8" },
  { key: "indeterminate", color: "#f5c542" },
];

export default function Observability({ data }) {
  const o = data.observability;
  if (!o) return <div className="loading">Artefact observability.json indisponible.</div>;

  const rows = Object.entries(o.states || {}).map(([sensor, counts]) => {
    const row = { sensor: SENSOR_LABELS[sensor] || sensor };
    for (const s of STATES) row[s.key] = counts[s.key] ?? 0;
    return row;
  });

  return (
    <div>
      <h2 className="page-title">Observabilité — stratégie à 4 états</h2>
      <p className="page-sub">
        Aucune cellule n'est jamais étiquetée « pas de feu ». Quatre états mutuellement exclusifs
        : détection observée / absence de détection en conditions d'observation plausibles /
        absence d'observation ou observabilité inconnue / indéterminé.
      </p>

      <div className="banner info">
        <strong>Produits de couverture d'observation acquis : {o.coverage_products_acquired ? "oui" : "non"}</strong>
        {o.note}
      </div>

      <div className="panel">
        <h3>
          États par capteur
          <span className="hint">grille {o.grid_deg}° · comptages calculés</span>
        </h3>
        <div className="chart-box tall">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ left: 10, right: 20, top: 10 }}>
              <CartesianGrid stroke="#23303f" strokeDasharray="3 3" />
              <XAxis dataKey="sensor" stroke="#8ba0b8" tick={{ fontSize: 12.5 }} />
              <YAxis allowDecimals={false} stroke="#8ba0b8" tick={{ fontSize: 11.5 }} />
              <Tooltip
                contentStyle={{
                  background: "#131b24",
                  border: "1px solid #23303f",
                  borderRadius: 8,
                }}
              />
              <Legend />
              {STATES.map((s) => (
                <Bar
                  key={s.key}
                  dataKey={s.key}
                  name={o.state_labels?.[s.key] || s.key}
                  fill={s.color}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="cards">
        {STATES.map((s) => (
          <div className="card" key={s.key}>
            <div className="k" style={{ color: s.color }}>
              ● {o.state_labels?.[s.key] || s.key}
            </div>
            <div className="v small mono">{s.key}</div>
            <div className="d">
              total :{" "}
              {fmt(rows.reduce((sum, r) => sum + (r[s.key] || 0), 0))} cellule(s) · capteur
            </div>
          </div>
        ))}
      </div>

      <div className="panel">
        <h3>
          Détail par capteur
          <span className="hint">aucun état « pas de feu » n'existe dans le schéma</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Capteur</th>
                {STATES.map((s) => (
                  <th key={s.key}>{o.state_labels?.[s.key] || s.key}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td className="txt">
                    <strong>{r.sensor}</strong>
                  </td>
                  {STATES.map((s) => (
                    <td key={s.key}>{fmt(r[s.key])}</td>
                  ))}
                  <td>
                    {fmt(STATES.reduce((sum, s) => sum + (r[s.key] || 0), 0))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
