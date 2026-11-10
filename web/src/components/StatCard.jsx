/**
 * StatCard - Component for displaying statistical metrics
 * Used by: Overview, Harmonization Lab, Data Catalog
 * 
 * @param {string} title - Card title
 * @param {number|string} value - Main value to display
 * @param {string} unit - Optional unit
 * @param {string} description - Optional description
 * @param {string} trend - Optional trend indicator
 */
import { fmt } from "../data.js";

export default function StatCard({ title, value, unit, description, trend }) {
  return (
    <div className="card">
      <div className="k">{title}</div>
      <div className="v">
        {typeof value === "number" ? fmt(value) : value}
        {unit && <span style={{ fontSize: "15px", color: "var(--muted)" }}> {unit}</span>}
      </div>
      {description && <div className="d">{description}</div>}
      {trend && (
        <div className="d" style={{ color: trend === "up" ? "var(--green)" : trend === "down" ? "var(--red)" : "var(--muted)" }}>
          {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}
        </div>
      )}
    </div>
  );
}
