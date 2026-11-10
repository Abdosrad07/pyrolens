/**
 * Methodology - View for scientific methodology documentation
 */
import LoadingState from "../components/LoadingState.jsx";

export default function Methodology() {
  return (
    <div>
      <h2 className="page-title">Méthodologie</h2>
      <p className="page-sub">
        Documentation scientifique des méthodes utilisées dans PyroLens.
      </p>
      <div className="panel">
        <LoadingState message="Chargement de la méthodologie…" />
      </div>
    </div>
  );
}
