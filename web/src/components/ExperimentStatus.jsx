/**
 * ExperimentStatus - Component for tracking experiment execution with polling
 * Used by: HarmonizationDetail
 * 
 * @param {string} jobId - Experiment job ID
 * @param {function} onComplete - Callback when experiment completes
 */
import { useState, useEffect } from "react";
import { getExperimentStatus } from "../data.js";

function statusPill(status) {
  if (status === "succeeded") return <span className="pill ok">succès</span>;
  if (status === "failed") return <span className="pill blocked">échoué</span>;
  if (status === "running") return <span className="pill ref">en cours</span>;
  if (status === "queued") return <span className="pill ref">en attente</span>;
  return <span className="pill ref">{status}</span>;
}

export default function ExperimentStatus({ jobId, onComplete }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    let intervalId;
    let alive = true;

    const poll = async () => {
      try {
        const result = await getExperimentStatus(jobId);
        if (alive) {
          setStatus(result);
          if (result.status === "succeeded" || result.status === "failed") {
            setPolling(false);
            if (onComplete) onComplete(result);
          }
        }
      } catch (err) {
        if (alive) {
          setError(err);
          setPolling(false);
        }
      }
    };

    poll();
    intervalId = setInterval(poll, 2000);

    return () => {
      alive = false;
      clearInterval(intervalId);
    };
  }, [jobId, onComplete]);

  if (error) {
    return (
      <div className="panel">
        <div className="banner warn">
          <strong>Erreur de suivi</strong>
          {error.message}
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="panel">
        <div className="loading">Chargement du statut…</div>
      </div>
    );
  }

  return (
    <div className="panel">
      <h3>Statut de l'expérience</h3>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
        <span style={{ fontSize: "18px", fontWeight: "bold" }}>
          {statusPill(status.status)}
        </span>
        {polling && <span className="muted small">(mise à jour automatique…)</span>}
      </div>
      <div className="table-wrap">
        <table className="data">
          <tbody>
            <tr>
              <td className="txt"><strong>ID de l'expérience</strong></td>
              <td className="mono small">{jobId}</td>
            </tr>
            <tr>
              <td className="txt"><strong>Créé le</strong></td>
              <td className="muted">{status.created_at}</td>
            </tr>
            {status.started_at && (
              <tr>
                <td className="txt"><strong>Démarré le</strong></td>
                <td className="muted">{status.started_at}</td>
              </tr>
            )}
            {status.finished_at && (
              <tr>
                <td className="txt"><strong>Terminé le</strong></td>
                <td className="muted">{status.finished_at}</td>
              </tr>
            )}
            {status.error && (
              <tr>
                <td className="txt"><strong>Erreur</strong></td>
                <td style={{ color: "var(--red)" }}>{status.error}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
