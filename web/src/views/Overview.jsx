import { fmt, SENSOR_LABELS } from "../data.js";

function OriginBanner({ origin }) {
  if (origin === "synthetic_fixture") {
    return (
      <div className="banner warn">
        <strong>Origine des données : échantillon synthétique de démonstration</strong>
        Les données NASA réelles n'ont pas pu être acquises dans cet environnement
        (blocages HTTP documentés ci-dessous). Tous les chiffres calculés ici proviennent
        d'un échantillon synthétique : ils valident le pipeline, ils ne sont **pas** des
        mesures du Cameroun. Aucune valeur antérieure v0.3 n'est présentée comme recalculée.
      </div>
    );
  }
  return (
    <div className="banner info">
      <strong>Origine des données : {origin}</strong>
      Valeurs calculées par le pipeline sur les données listées dans l'inventaire.
    </div>
  );
}

function statusPill(status) {
  const norm = String(status ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  if (norm === "ok") return <span className="pill ok">ok</span>;
  if (norm === "bloque" || norm === "blocked")
    return <span className="pill blocked">bloqué</span>;
  return <span className="pill ref">{status}</span>;
}

export default function Overview({ data }) {
  const exec = data.execution || {};
  const steps = exec.steps || [];
  const blockers = exec.blockers || [];
  const inv = data.inventory;
  const dl = data.downloads;

  const nOk = steps.filter((s) => s.status === "ok").length;
  const origin = data.audit?.data_origin || "—";

  return (
    <div>
      <h2 className="page-title">Synthèse d'exécution</h2>
      <p className="page-sub">
        État réel de la chaîne {exec.project_version || "pyrolens"} : chaque étape est
        attestée par un artefact produit ; les blocages d'accès aux données sont listés
        sans être présentés comme acquis.
      </p>

      <OriginBanner origin={origin} />

      <div className="cards">
        <div className="card">
          <div className="k">Étapes exécutées</div>
          <div className="v">
            {nOk}
            <span style={{ fontSize: 15, color: "var(--muted)" }}> / {steps.length}</span>
          </div>
          <div className="d">statut « ok »</div>
        </div>
        <div className="card">
          <div className="k">Blocages documentés</div>
          <div className="v" style={{ color: blockers.length ? "var(--red)" : undefined }}>
            {blockers.length}
          </div>
          <div className="d">accès données réelles</div>
        </div>
        <div className="card">
          <div className="k">Période cible</div>
          <div className="v small mono">
            {exec.period_start} → {exec.period_end}
          </div>
          <div className="d">conforme au plan</div>
        </div>
        <div className="card">
          <div className="k">Origine des données</div>
          <div className="v small">{origin}</div>
          <div className="d">étiqueté dans chaque JSON</div>
        </div>
        <div className="card">
          <div className="k">Fichiers téléchargés</div>
          <div className="v">{dl?.entry_count ?? "—"}</div>
          <div className="d">manifeste SHA-256</div>
        </div>
      </div>

      <div className="panel">
        <h3>
          Étapes du pipeline
          <span className="hint">journalisé dans reports/logs/</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Étape</th>
                <th>Statut</th>
                <th>Preuve / détail</th>
                <th>Horodatage</th>
              </tr>
            </thead>
            <tbody>
              {steps.map((s, i) => (
                <tr key={i}>
                  <td className="txt">
                    <strong>{s.step}</strong>
                  </td>
                  <td>{statusPill(s.status)}</td>
                  <td className="txt">{s.detail}</td>
                  <td className="muted">{(s.at || "").slice(0, 19)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {blockers.length > 0 && (
        <div className="panel">
          <h3>
            Blocages d'accès aux données
            <span className="hint">aucun contournement d'authentification</span>
          </h3>
          {blockers.map((b, i) => (
            <div className="blocker" key={i}>
              <div className="what">
                {b.what}{" "}
                {b.http_status ? <span className="pill blocked">HTTP {b.http_status}</span> : null}
              </div>
              <div className="detail">{b.detail}</div>
              <div className="action">
                <strong>Action attendue :</strong> {b.action}
              </div>
            </div>
          ))}
        </div>
      )}

      {inv && (
        <div className="panel">
          <h3>
            Inventaire FIRMS / CMR
            <span className="hint">vérifié avant tout téléchargement massif</span>
          </h3>
          <p className="muted small" style={{ marginTop: 0 }}>
            Source : {inv.source} — {inv.base_url} · période vérifiée {inv.period?.start} →{" "}
            {inv.period?.end}
            {inv.bbox_note ? ` · ${inv.bbox_note}` : ""}
          </p>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Capteur</th>
                  <th>Short name (CMR)</th>
                  <th>Version retenue</th>
                  <th>Années disponibles</th>
                  <th>Granules 2019 (bbox)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(inv.sensors || {}).map(([key, s]) => (
                  <tr key={key}>
                    <td className="txt">
                      <strong>{s.label || SENSOR_LABELS[key] || key}</strong>
                    </td>
                    <td>{s.short_name}</td>
                    <td>{s.version_used || s.configured_version}</td>
                    <td>
                      {Array.isArray(s.years)
                        ? `${s.years.length} ans (${s.years[0]}–${s.years[s.years.length - 1]})`
                        : "—"}
                    </td>
                    <td>{fmt(s.sample_granules_2019)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {dl && dl.by_status && dl.by_status.length > 0 && (
        <div className="panel">
          <h3>
            Manifeste de téléchargement (agrégat)
            <span className="hint">{dl.entry_count} entrées — détail complet dans downloads.json sur disque</span>
          </h3>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Statut</th>
                  <th>Entrées</th>
                  <th>Acquises</th>
                  <th>Détail</th>
                </tr>
              </thead>
              <tbody>
                {dl.by_status.map((s, i) => (
                  <tr key={i}>
                    <td className="txt">{s.status}</td>
                    <td>{fmt(s.count)}</td>
                    <td>{s.acquired ? fmt(s.count) : "0"}</td>
                    <td className="txt muted">
                      {s.status === "blocked_earthdata_login"
                        ? "Clés Earthdata requises (D4)"
                        : s.status === "blocked_missing_credential"
                        ? "Clé FIRMS requise"
                        : s.status === "deferred"
                        ? "Budget de commande atteint — repris à l'exécution suivante"
                        : s.status === "already_present"
                        ? "Déjà présent sur disque"
                        : s.status === "downloaded"
                        ? "Téléchargé avec succès"
                        : s.status === "http_error"
                        ? "Erreur HTTP — consultez downloads.json"
                        : s.status === "error"
                        ? "Erreur de traitement — consultez downloads.json"
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {dl.coverage_products_acquired === false && (
            <p className="muted small">
              Produits de couverture/nuages non acquis : observabilité par défaut « inconnue ».
            </p>
          )}
        </div>
      )}
    </div>
  );
}
