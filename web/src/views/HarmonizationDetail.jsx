/**
 * HarmonizationDetail - View for experiment details and results
 */
import { useState } from "react";
import { getExperimentResult, PAIR_LABELS, fmt } from "../data.js";
import ExperimentStatus from "../components/ExperimentStatus.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import MetricCard from "../components/MetricCard.jsx";
import ResultTable from "../components/ResultTable.jsx";

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
        <div>
          {/* Section 1: Provenance */}
          <div className="panel">
            <h3>Provenance des données</h3>
            <div className="table-wrap">
              <table className="data">
                <tbody>
                  <tr>
                    <td className="txt"><strong>Origine</strong></td>
                    <td>{result.data_origin}</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Généré le</strong></td>
                    <td>{result.generated_at}</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Durée d'exécution</strong></td>
                    <td>{fmt(result.elapsed_s, 2)} s</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Digest SHA-256</strong></td>
                    <td className="mono small">{result.digest_sha256}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: Parameters */}
          <div className="panel">
            <h3>Paramètres de l'expérience</h3>
            <div className="table-wrap">
              <table className="data">
                <tbody>
                  <tr>
                    <td className="txt"><strong>Paire</strong></td>
                    <td>{PAIR_LABELS[result.params?.pair] || result.params?.pair}</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Résolution de grille</strong></td>
                    <td>{result.params?.grid_deg}°</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Fenêtre temporelle</strong></td>
                    <td>{result.params?.window_days} jours</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Source</strong></td>
                    <td>{result.params?.source}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Main Metrics */}
          {result.result && (
            <div className="panel">
              <h3>Métriques principales</h3>
              <div className="cards">
                <MetricCard
                  label="Détections A"
                  value={result.result.n_a}
                  unit="cellules"
                  description="Capteur A"
                />
                <MetricCard
                  label="Détections B"
                  value={result.result.n_b}
                  unit="cellules"
                  description="Capteur B"
                />
                <MetricCard
                  label="Intersection"
                  value={result.result.intersection}
                  unit="cellules"
                  description="Cellules communes"
                />
                <MetricCard
                  label="Union"
                  value={result.result.union}
                  unit="cellules"
                  description="Total unique"
                />
                <MetricCard
                  label="Indice de Jaccard"
                  value={result.result.jaccard}
                  description="Recouvrement relatif"
                />
              </div>
              <p className="muted small" style={{ marginTop: "12px" }}>
                <strong>Note :</strong> L'indice de Jaccard mesure le recouvrement relatif entre les deux capteurs.
                Une valeur élevée indique une forte similarité spatiale/temporelle des détections.
              </p>
            </div>
          )}

          {/* Section 4: Monthly Divergence */}
          {result.result?.monthly && result.result.monthly.length > 0 && (
            <div className="panel">
              <h3>Divergence mensuelle</h3>
              <ResultTable
                columns={[
                  { key: "month", label: "Mois" },
                  { key: "only_a", label: "A seulement" },
                  { key: "only_b", label: "B seulement" },
                  { key: "common", label: "Commun" },
                ]}
                data={result.result.monthly}
                formatCell={(key, value) => {
                  if (key === "month") return value;
                  return fmt(value);
                }}
              />
            </div>
          )}

          {/* Section 5: Spatial Top */}
          {result.result?.spatial_top && result.result.spatial_top.length > 0 && (
            <div className="panel">
              <h3>Distribution spatiale (top cellules)</h3>
              <ResultTable
                columns={[
                  { key: "cell_id", label: "Cellule" },
                  { key: "count_a", label: "A" },
                  { key: "count_b", label: "B" },
                  { key: "common", label: "Commun" },
                ]}
                data={result.result.spatial_top}
                formatCell={(key, value) => {
                  if (key === "cell_id") return value;
                  return fmt(value);
                }}
              />
            </div>
          )}

          {/* Section 6: Source Statistics */}
          {result.source && (
            <div className="panel">
              <h3>Statistiques de la source</h3>
              <div className="table-wrap">
                <table className="data">
                  <tbody>
                    <tr>
                      <td className="txt"><strong>Fichiers</strong></td>
                      <td>{fmt(result.source.n_files)}</td>
                    </tr>
                    <tr>
                      <td className="txt"><strong>Lignes totales</strong></td>
                      <td>{fmt(result.source.n_rows_total)}</td>
                    </tr>
                    <tr>
                      <td className="txt"><strong>Lignes analysables</strong></td>
                      <td>{fmt(result.source.n_rows_analyzable)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Section 7: Software Version */}
          {result.software && (
            <div className="panel">
              <h3>Version du logiciel</h3>
              <p className="muted">{result.software}</p>
            </div>
          )}

          {/* Section 8: Warnings */}
          {result.warning && (
            <div className="panel">
              <div className="banner warn">
                <strong>Avertissement</strong>
                {result.warning}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
