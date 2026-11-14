/**
 * HarmonizationList - Main view for Harmonization Lab
 * Lists all experiments with filtering and creation link
 */
import { useState, useEffect } from "react";
import { loadExperiments } from "../data.js";
import LoadingState from "../components/LoadingState.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import ExperimentList from "../components/ExperimentList.jsx";

export default function HarmonizationList({ data }) {
  const [experiments, setExperiments] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    loadExperiments()
      .then((result) => {
        if (alive) {
          setExperiments(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (alive) {
          setError(err);
          setLoading(false);
        }
      });
    return () => {
      alive = false;
    };
  }, []);

  const handleSelect = (jobId) => {
    window.location.hash = `harmonization-${jobId}`;
  };

  const handleCreate = () => {
    window.location.hash = "harmonization-new";
  };

  if (loading) {
    return (
      <div>
        <h2 className="page-title">Harmonization Lab</h2>
        <p className="page-sub">
          Créez et suivez les expériences d'harmonisation entre capteurs satellites.
        </p>
        <div className="panel">
          <LoadingState message="Chargement des expériences…" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="page-title">Harmonization Lab</h2>
        <p className="page-sub">
          Créez et suivez les expériences d'harmonisation entre capteurs satellites.
        </p>
        <ErrorState error={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  return (
    <div>
      <h2 className="page-title">Harmonization Lab</h2>
      <p className="page-sub">
        Créez et suivez les expériences d'harmonisation entre capteurs satellites.
      </p>
      <div className="panel">
        {experiments && experiments.length === 0 ? (
          <EmptyState message="Aucune expérience disponible. Créez votre première expérience pour commencer." />
        ) : (
          <ExperimentList experiments={experiments} onSelect={handleSelect} onCreate={handleCreate} />
        )}
      </div>
    </div>
  );
}
