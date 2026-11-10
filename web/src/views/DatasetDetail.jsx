/**
 * DatasetDetail - View for dataset details
 */
export default function DatasetDetail({ datasetId }) {
  return (
    <div>
      <h2 className="page-title">Détail du jeu de données</h2>
      <p className="page-sub">
        Métadonnées et informations sur {datasetId}.
      </p>
      <div className="panel">
        <p className="muted">Détail du jeu de données - à implémenter</p>
      </div>
    </div>
  );
}
