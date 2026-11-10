/**
 * DataCatalog - Main view for Data & Methodology module
 * Lists all available datasets
 */
import LoadingState from "../components/LoadingState.jsx";

export default function DataCatalog({ data }) {
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
