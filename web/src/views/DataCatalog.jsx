/**
 * DataCatalog - Main view for Data & Methodology module
 * Lists all available datasets
 */
import { useState, useEffect } from "react";
import { loadCatalog, fmt } from "../data.js";
import LoadingState from "../components/LoadingState.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";

export default function DataCatalog({ data }) {
  const [catalog, setCatalog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    loadCatalog()
      .then((result) => {
        if (alive) {
          setCatalog(result);
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

  const handleSelect = (datasetId) => {
    window.location.hash = `data-${datasetId}`;
  };

  if (loading) {
    return (
      <div>
        <h2 className="page-title">Catalogue de données</h2>
        <p className="page-sub">
          Explorez les jeux de données disponibles et leurs métadonnées.
        </p>
        <div className="panel">
          <LoadingState message="Chargement du catalogue…" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="page-title">Catalogue de données</h2>
        <p className="page-sub">
          Explorez les jeux de données disponibles et leurs métadonnées.
        </p>
        <ErrorState error={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  const datasets = catalog?.datasets || [];

  return (
    <div>
      <h2 className="page-title">Catalogue de données</h2>
      <p className="page-sub">
        Explorez les jeux de données disponibles et leurs métadonnées.
      </p>

      {catalog?.provenance && (
        <div className="panel">
          <h3>Provenance du catalogue</h3>
          <div className="table-wrap">
            <table className="data">
              <tbody>
                <tr>
                  <td className="txt"><strong>Manifeste</strong></td>
                  <td>{catalog.provenance.manifest}</td>
                </tr>
                <tr>
                  <td className="txt"><strong>Statut d'acquisition</strong></td>
                  <td>{catalog.provenance.status}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="panel">
        <h3>Jeux de données ({datasets.length})</h3>
        {datasets.length === 0 ? (
          <EmptyState message="Aucun jeu de données disponible" />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Période</th>
                  <th>Enregistrements</th>
                  <th>Anomalies</th>
                  <th>Disponible</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((ds) => (
                  <tr key={ds.id}>
                    <td className="txt">
                      <strong>{ds.id}</strong>
                    </td>
                    <td>{ds.type}</td>
                    <td className="muted small">
                      {ds.period_start} → {ds.period_end}
                    </td>
                    <td>{fmt(ds.n_records)}</td>
                    <td style={{ color: ds.n_anomalies > 0 ? "var(--amber)" : undefined }}>
                      {fmt(ds.n_anomalies)}
                    </td>
                    <td>
                      {ds.available ? (
                        <span className="pill ok">oui</span>
                      ) : (
                        <span className="pill blocked">non</span>
                      )}
                    </td>
                    <td>
                      <button
                        className="linkish"
                        onClick={() => handleSelect(ds.id)}
                      >
                        Voir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
