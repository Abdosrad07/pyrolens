/**
 * DatasetDetail - View for dataset details
 */
import { useState, useEffect } from "react";
import { loadDatasetDetail, fmt } from "../data.js";
import LoadingState from "../components/LoadingState.jsx";
import ErrorState from "../components/ErrorState.jsx";

export default function DatasetDetail({ datasetId }) {
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    loadDatasetDetail(datasetId)
      .then((result) => {
        if (alive) {
          setDataset(result);
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
  }, [datasetId]);

  const handleBack = () => {
    window.location.hash = "data";
  };

  if (loading) {
    return (
      <div>
        <h2 className="page-title">Détail du jeu de données</h2>
        <p className="page-sub">
          Métadonnées et informations sur <span className="mono">{datasetId}</span>.
        </p>
        <div className="panel">
          <LoadingState message="Chargement des détails…" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="page-title">Détail du jeu de données</h2>
        <p className="page-sub">
          Métadonnées et informations sur <span className="mono">{datasetId}</span>.
        </p>
        <ErrorState error={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <h2 className="page-title">Détail du jeu de données</h2>
          <p className="page-sub">
            Métadonnées et informations sur <span className="mono">{datasetId}</span>.
          </p>
        </div>
        <button className="btn" onClick={handleBack}>
          ← Retour
        </button>
      </div>

      {/* Section 1: Metadata */}
      <div className="panel">
        <h3>Métadonnées</h3>
        <div className="table-wrap">
          <table className="data">
            <tbody>
              <tr>
                <td className="txt"><strong>ID</strong></td>
                <td className="mono">{dataset.id}</td>
              </tr>
              <tr>
                <td className="txt"><strong>Type</strong></td>
                <td>{dataset.type}</td>
              </tr>
              <tr>
                <td className="txt"><strong>Période</strong></td>
                <td className="muted">{dataset.period_start} → {dataset.period_end}</td>
              </tr>
              <tr>
                <td className="txt"><strong>Enregistrements totaux</strong></td>
                <td>{fmt(dataset.n_records)}</td>
              </tr>
              <tr>
                <td className="txt"><strong>Anomalies</strong></td>
                <td style={{ color: dataset.n_anomalies > 0 ? "var(--amber)" : undefined }}>
                  {fmt(dataset.n_anomalies)}
                </td>
              </tr>
              <tr>
                <td className="txt"><strong>Généré le</strong></td>
                <td className="muted">{dataset.generated_at}</td>
              </tr>
              <tr>
                <td className="txt"><strong>Origine</strong></td>
                <td>{dataset.data_origin}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 2: Files (for source datasets) */}
      {dataset.files && dataset.files.length > 0 && (
        <div className="panel">
          <h3>Fichiers ({dataset.files.length})</h3>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Fichier</th>
                  <th>Enregistrements</th>
                  <th>Anomalies</th>
                  <th>Date min</th>
                  <th>Date max</th>
                </tr>
              </thead>
              <tbody>
                {dataset.files.map((file, i) => (
                  <tr key={i}>
                    <td className="mono small">{file.name}</td>
                    <td>{fmt(file.n_records)}</td>
                    <td style={{ color: file.n_anomalies > 0 ? "var(--amber)" : undefined }}>
                      {fmt(file.n_anomalies)}
                    </td>
                    <td className="muted small">{file.date_min}</td>
                    <td className="muted small">{file.date_max}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Section 3: Artifact info (for derived datasets) */}
      {dataset.artifact && (
        <div className="panel">
          <h3>Artefact</h3>
          <div className="table-wrap">
            <table className="data">
              <tbody>
                <tr>
                  <td className="txt"><strong>Fichier</strong></td>
                  <td className="mono">{dataset.artifact}</td>
                </tr>
                <tr>
                  <td className="txt"><strong>Disponible</strong></td>
                  <td>
                    {dataset.available ? (
                      <span className="pill ok">oui</span>
                    ) : (
                      <span className="pill blocked">non</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Section 4: Anomaly details */}
      {dataset.n_anomalies > 0 && (
        <div className="panel">
          <div className="banner warn">
            <strong>Anomalies détectées</strong>
            Ce jeu de données contient {fmt(dataset.n_anomalies)} anomalie(s). Consultez le rapport d'audit pour plus de détails.
          </div>
        </div>
      )}
    </div>
  );
}
