/**
 * MetricCard - Component for displaying a single metric
 * Used by: ExperimentDetail
 * 
 * @param {string} label - Metric label
 * @param {number|string} value - Metric value
 * @param {string} unit - Optional unit
 * @param {string} description - Optional description
 */
import { fmt } from "../data.js";

export default function MetricCard({ label, value, unit, description }) {
  return (
    <div className="card">
      <div className="k">{label}</div>
      <div className="v">
        {typeof value === "number" ? fmt(value) : value}
        {unit && <span style={{ fontSize: "15px", color: "var(--muted)" }}> {unit}</span>}
      </div>
      {description && <div className="d">{description}</div>}
    </div>
  );
}
