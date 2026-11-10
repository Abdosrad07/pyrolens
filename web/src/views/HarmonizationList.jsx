/**
 * HarmonizationList - Main view for Harmonization Lab
 * Lists all experiments with filtering and creation link
 */
import LoadingState from "../components/LoadingState.jsx";
import EmptyState from "../components/EmptyState.jsx";

export default function HarmonizationList({ data }) {
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
