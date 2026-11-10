/**
 * ExportButton - Component for exporting experiment results
 * Used by: HarmonizationDetail
 * 
 * @param {string} jobId - Experiment job ID
 * @param {string} format - Export format (csv, json)
 * @param {string} label - Button label
 */
import { useState } from "react";
import { exportData } from "../data.js";

export default function ExportButton({ jobId, format = "csv", label = "Exporter" }) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);
    try {
      const blob = await exportData({ job_id: jobId, format });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `experiment_${jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <button
        className="btn"
        onClick={handleExport}
        disabled={exporting}
        style={{ opacity: exporting ? 0.6 : 1 }}
      >
        {exporting ? "Export en cours…" : label}
      </button>
      {error && (
        <div className="banner warn" style={{ marginTop: "8px" }}>
          <strong>Erreur d'export</strong>
          {error.message}
        </div>
      )}
    </div>
  );
}
