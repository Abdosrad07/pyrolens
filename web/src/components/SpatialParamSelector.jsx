/**
 * SpatialParamSelector - Component for selecting spatial parameters
 * Used by: ExperimentForm
 * 
 * @param {number} gridDeg - Grid resolution in degrees
 * @param {function} onChange - Callback when grid changes
 */
export default function SpatialParamSelector({ gridDeg = 0.25, onChange }) {
  const GRID_OPTIONS = [0.1, 0.25, 0.5];

  return (
    <div className="controls">
      <label htmlFor="grid-select">Résolution de grille</label>
      <select
        id="grid-select"
        value={gridDeg}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: "100%", maxWidth: "400px" }}
      >
        {GRID_OPTIONS.map((g) => (
          <option key={g} value={g}>
            {g}° ({(g * 111).toFixed(1)} km approx.)
          </option>
        ))}
      </select>
      <p className="muted small" style={{ marginTop: "4px" }}>
        La résolution de la grille détermine la taille des cellules pour l'agrégation spatiale.
      </p>
    </div>
  );
}
