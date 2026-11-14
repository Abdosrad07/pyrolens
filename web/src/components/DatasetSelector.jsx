/**
 * DatasetSelector - Component for selecting datasets
 * Used by: ExperimentForm
 * 
 * @param {Array} datasets - Available datasets
 * @param {string} selected - Currently selected dataset
 * @param {function} onChange - Callback when selection changes
 */
export default function DatasetSelector({ datasets = [], selected, onChange }) {
  return (
    <div className="controls">
      <label htmlFor="dataset-select">Jeu de données source</label>
      <select
        id="dataset-select"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: "100%", maxWidth: "400px" }}
      >
        <option value="">-- Sélectionner --</option>
        {datasets.map((ds) => (
          <option key={ds.id} value={ds.id}>
            {ds.label || ds.id}
          </option>
        ))}
      </select>
      <p className="muted small" style={{ marginTop: "4px" }}>
        Sélectionnez le jeu de données source pour l'expérience.
      </p>
    </div>
  );
}
