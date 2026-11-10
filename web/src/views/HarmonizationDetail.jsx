/**
 * HarmonizationDetail - View for experiment details and results
 */
import { useState } from "react";
import { getExperimentResult } from "../data.js";
import ExperimentStatus from "../components/ExperimentStatus.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorState from "../components/ErrorState.jsx";

export default function HarmonizationDetail({ jobId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleComplete = async (status) => {
    if (status.status === "succeeded") {
      try {
        const data = await getExperimentResult(jobId);
        setResult(data);
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
      }
    } else if (status.status === "failed") {
      setError(new Error(status.error || "L'expérience a échoué"));
      setLoading(false);
    }
  };

  const handleBack = () => {
    window.location.hash = "harmonization";
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <h2 className="page-title">Détail de l'expérience</h2>
          <p className="page-sub">
            Résultats et métriques de l'expérience <span className="mono">{jobId}</span>.
          </p>
        </div>
        <button className="btn" onClick={handleBack}>
          ← Retour
        </button>
      </div>

      <ExperimentStatus jobId={jobId} onComplete={handleComplete} />

      {loading && (
        <div className="panel">
          <LoadingState message="Chargement des résultats…" />
        </div>
      )}

      {error && <ErrorState error={error} />}

      {result && (
        <div className="panel">
          <h3>Résultats</h3>
          <p className="muted">Résultats détaillés - à implémenter dans le prochain commit</p>
        </div>
      )}
    </div>
  );
}
