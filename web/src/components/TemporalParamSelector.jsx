/**
 * TemporalParamSelector - Component for selecting temporal parameters
 * Used by: ExperimentForm
 * 
 * @param {number} windowDays - Window size in days
 * @param {function} onChange - Callback when window changes
 */
export default function TemporalParamSelector({ windowDays = 8, onChange }) {
  const WINDOW_OPTIONS = [4, 8, 16];

  return (
    <div className="controls">
      <label htmlFor="window-select">Fenêtre temporelle</label>
      <select
        id="window-select"
        value={windowDays}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        style={{ width: "100%", maxWidth: "400px" }}
      >
        {WINDOW_OPTIONS.map((w) => (
          <option key={w} value={w}>
            {w} jours
          </option>
        ))}
      </select>
      <p className="muted small" style={{ marginTop: "4px" }}>
        La fenêtre temporelle détermine l'intervalle d'agrégation pour les détections.
      </p>
    </div>
  );
}
