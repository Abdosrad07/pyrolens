/**
 * SatelliteSelector - Component for selecting satellites
 * Used by: Overview, Fire Calendar, Harmonization Lab, Data Catalog
 * 
 * @param {Array} satellites - Available satellites (e.g., ['terra', 'aqua', 'viirs_snpp'])
 * @param {Array} selected - Currently selected satellites
 * @param {function} onChange - Callback when selection changes
 * @param {boolean} multiple - Allow multiple selection (default: true)
 */
import { SENSOR_LABELS } from "../data.js";

export default function SatelliteSelector({
  satellites = ["terra", "aqua", "viirs_snpp"],
  selected = [],
  onChange,
  multiple = true,
}) {
  const toggleSatellite = (satellite) => {
    if (multiple) {
      if (selected.includes(satellite)) {
        onChange(selected.filter((s) => s !== satellite));
      } else {
        onChange([...selected, satellite]);
      }
    } else {
      onChange([satellite]);
    }
  };

  return (
    <div className="controls">
      <label>Satellites</label>
      <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
        {satellites.map((satellite) => (
          <label
            key={satellite}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            <input
              type={multiple ? "checkbox" : "radio"}
              checked={selected.includes(satellite)}
              onChange={() => toggleSatellite(satellite)}
              name="satellite-selector"
            />
            {SENSOR_LABELS[satellite] || satellite}
          </label>
        ))}
      </div>
    </div>
  );
}
