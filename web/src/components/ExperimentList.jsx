/**
 * ExperimentList - Component for displaying experiments table
 * Used by: HarmonizationList
 * 
 * @param {Array} experiments - Array of experiment objects
 * @param {function} onSelect - Callback when an experiment is selected
 * @param {function} onCreate - Callback to create new experiment
 */
import { fmt, PAIR_LABELS } from "../data.js";
import Pagination, { usePaged } from "./Pagination.jsx";

function statusPill(status) {
  if (status === "succeeded") return <span className="pill ok">succès</span>;
  if (status === "failed") return <span className="pill blocked">échoué</span>;
  if (status === "running") return <span className="pill ref">en cours</span>;
  if (status === "queued") return <span className="pill ref">en attente</span>;
  return <span className="pill ref">{status}</span>;
}

export default function ExperimentList({ experiments = [], onSelect, onCreate }) {
  const expPage = usePaged(experiments, 10);

  if (experiments.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "40px 20px" }}>
        <p className="muted">Aucune expérience disponible</p>
        {onCreate && (
          <button className="btn" onClick={onCreate} style={{ marginTop: "12px" }}>
            Créer une expérience
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "12px" }}>
        {onCreate && (
          <button className="btn" onClick={onCreate}>
            + Nouvelle expérience
          </button>
        )}
      </div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>Paire</th>
              <th>Grille</th>
              <th>Fenêtre</th>
              <th>Statut</th>
              <th>Créé le</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {expPage.pageItems.map((exp) => (
              <tr key={exp.job_id}>
                <td className="mono small">{exp.job_id?.slice(0, 8)}…</td>
                <td className="txt">{PAIR_LABELS[exp.params?.pair] || exp.params?.pair}</td>
                <td>{exp.params?.grid_deg}°</td>
                <td>{exp.params?.window_days} j</td>
                <td>{statusPill(exp.status)}</td>
                <td className="muted small">{exp.created_at?.slice(0, 10)}</td>
                <td>
                  <button
                    className="linkish"
                    onClick={() => onSelect && onSelect(exp.job_id)}
                  >
                    Voir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        page={expPage.page}
        totalPages={expPage.totalPages}
        total={expPage.total}
        pageSize={expPage.pageSize}
        onPageChange={expPage.setPage}
      />
    </div>
  );
}
