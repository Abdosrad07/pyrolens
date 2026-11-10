/**
 * HarmonizationDetail - View for experiment details and results
 */
export default function HarmonizationDetail({ jobId }) {
  return (
    <div>
      <h2 className="page-title">Détail de l'expérience</h2>
      <p className="page-sub">
        Résultats et métriques de l'expérience {jobId}.
      </p>
      <div className="panel">
        <p className="muted">Détail de l'expérience - à implémenter</p>
      </div>
    </div>
  );
}
