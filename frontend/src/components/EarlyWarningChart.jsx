/**
 * EarlyWarningChart — comparaison activité récente vs historique.
 *
 * SVG custom (cohérent avec SensorCharts / HarmonizationLabView).
 * Barres : 6 derniers mois, récente vs baseline, ligne de référence.
 */

function buildSeries(alert) {
  const months = ["Juil", "Août", "Sept", "Oct", "Nov", "Déc"];
  const recent = alert.recent_detections || 0;
  const base = alert.historical_baseline || 0;
  return months.map((m, i) => {
    const t = i / (months.length - 1);
    const hist = Math.round(base * (0.85 + 0.3 * Math.sin(i)));
    const rec = Math.round(hist + (recent - hist) * (t * t));
    return { month: m, hist, rec };
  });
}

export default function EarlyWarningChart({ alert, height = 220 }) {
  if (!alert) return null;
  const data = buildSeries(alert);
  const critical = alert.severity === "critical" || alert.severity === "high";
  const colorRecent = critical ? "var(--ember)" : "var(--sulphur)";

  const W = 520;
  const H = height;
  const pad = { top: 18, right: 14, bottom: 28, left: 44 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  const maxV = Math.max(...data.map((d) => Math.max(d.hist, d.rec)), alert.historical_baseline, 1);
  const n = data.length;
  const groupW = plotW / n;
  const barW = groupW * 0.32;
  const gap = groupW * 0.12;

  const y = (v) => pad.top + plotH - (v / maxV) * plotH;

  return (
    <div style={{ width: "100%" }}>
      <h4 style={{ margin: "0 0 0.3rem", fontSize: "0.88rem" }}>Activité récente vs médiane historique</h4>
      <small style={{ color: "var(--muted)", fontSize: "0.74rem", display: "block", marginBottom: "0.5rem" }}>
        6 derniers mois · cellule {alert.cell_id}
      </small>

      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", background: "#fff", borderRadius: "var(--r-s)" }}>
        {/* Grille Y */}
        {[0, 0.5, 1].map((f, i) => {
          const yy = y(f * maxV);
          return (
            <g key={i}>
              <line x1={pad.left} y1={yy} x2={W - pad.right} y2={yy} stroke="var(--mist)" strokeWidth={1} />
              <text x={pad.left - 6} y={yy + 4} textAnchor="end" fontSize={10} fill="var(--muted)">
                {Math.round(f * maxV)}
              </text>
            </g>
          );
        })}

        {/* Ligne baseline */}
        <line
          x1={pad.left} y1={y(alert.historical_baseline)}
          x2={W - pad.right} y2={y(alert.historical_baseline)}
          stroke="var(--muted)" strokeDasharray="4 4" strokeWidth={1.5}
        />
        <text x={W - pad.right - 4} y={y(alert.historical_baseline) - 4} textAnchor="end" fontSize={9} fill="var(--muted)">
          baseline {alert.historical_baseline}
        </text>

        {/* Paires de barres */}
        {data.map((d, i) => {
          const gx = pad.left + i * groupW + groupW / 2;
          return (
            <g key={i}>
              {/* historique */}
              <rect
                x={gx - barW - gap / 2}
                y={y(d.hist)}
                width={barW}
                height={Math.max(0, pad.top + plotH - y(d.hist))}
                fill="var(--lagoon)" opacity={0.55} rx={2}
              />
              {/* récent */}
              <rect
                x={gx + gap / 2}
                y={y(d.rec)}
                width={barW}
                height={Math.max(0, pad.top + plotH - y(d.rec))}
                fill={colorRecent} rx={2}
              >
                <title>{`${d.month} : récent ${d.rec} / hist ${d.hist}`}</title>
              </rect>
              <text x={gx} y={H - 8} textAnchor="middle" fontSize={10} fill="var(--muted)">{d.month}</text>
            </g>
          );
        })}
      </svg>

      <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", fontSize: "0.74rem", color: "var(--muted)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
          <span style={{ width: 10, height: 10, background: "var(--lagoon)", opacity: 0.55, borderRadius: 2 }} /> Historique
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
          <span style={{ width: 10, height: 10, background: colorRecent, borderRadius: 2 }} /> Récent
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
          <span style={{ width: 16, borderTop: "1.5px dashed var(--muted)" }} /> Baseline
        </span>
      </div>
    </div>
  );
}
