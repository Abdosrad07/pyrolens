/**
 * DqView — rapport de qualité des données RÉEL (artefact audit.json).
 *
 * Props: { onClose: () => void }
 * Source : /artifacts/audit.json (pipeline pyrolens audit) — jamais de mock.
 */

import { useState, useEffect } from "react";
import { useI18n } from "../i18n/index.jsx";

const PAGE = 15;

export default function DqView({ onClose }) {
  const { t } = useI18n();
  const [audit, setAudit] = useState(null);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetch("/artifacts/audit.json")
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setAudit)
      .catch((e) => setError(e.message));
  }, []);

  if (error)
    return (
      <div className="dq-card">
        <div className="dq-top">
          <h3>{t("dq.title")}</h3>
          <button className="ibtn" type="button" aria-label="Fermer" onClick={onClose}>✕</button>
        </div>
        <div className="banner err">Artefact audit.json indisponible : {error}</div>
      </div>
    );
  if (!audit)
    return (
      <div className="dq-card">
        <div className="dq-top">
          <h3>{t("dq.title")}</h3>
          <button className="ibtn" type="button" aria-label="Fermer" onClick={onClose}>✕</button>
        </div>
        <p className="empty">{t("dq.loading", "Chargement…")}</p>
      </div>
    );

  const anomalies = audit.anomalies_by_category || {};
  const classes = audit.rows_by_classification || {};
  const gaps = audit.temporal_gaps?.entries || [];
  const missing = audit.missing_values_by_column || {};
  const totalPages = Math.max(1, Math.ceil(gaps.length / PAGE));
  const slice = gaps.slice((page - 1) * PAGE, page * PAGE);

  return (
    <div className="dq-card">
      <div className="dq-top">
        <h3>Rapport de qualité des données</h3>
        <button className="ibtn" type="button" aria-label="Fermer le rapport" onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="dq-meta">
        {audit.n_files} fichiers · origine {audit.data_origin} · généré le{" "}
        {audit.generated_at ? new Date(audit.generated_at).toLocaleString("fr-FR") : "?"}
      </div>

      {audit.interpretation_warning && (
        <div className="banner warn" style={{ margin: "0.8rem 0" }}>
          {audit.interpretation_warning}
        </div>
      )}

      <div className="cards" style={{ margin: "1rem 0" }}>
        <div className="card">
          <div className="k">Fichiers audités</div>
          <div className="v">{audit.n_files}</div>
          <div className="u">{audit.data_origin}</div>
        </div>
        <div className="card">
          <div className="k">Anomalies</div>
          <div className="v">{Object.values(anomalies).reduce((a, b) => a + b, 0).toLocaleString("fr-FR")}</div>
          <div className="u">{Object.keys(anomalies).join(", ") || "aucune"}</div>
        </div>
        <div className="card">
          <div className="k">Lignes classifiées</div>
          <div className="v">{Object.entries(classes).map(([k, v]) => `${k}: ${v.toLocaleString("fr-FR")}`).join(" · ") || "—"}</div>
          <div className="u">classification rigoureuse</div>
        </div>
        <div className="card">
          <div className="k">Jours sans enregistrement</div>
          <div className="v">{audit.temporal_gaps?.n_entries ?? 0}</div>
          <div className="u">trous temporels capteurs</div>
        </div>
      </div>

      <h4 style={{ margin: "1rem 0 0.4rem" }}>Anomalies par catégorie</h4>
      <table className="dt">
        <thead><tr><th>Catégorie</th><th>Nombre</th></tr></thead>
        <tbody>
          {Object.entries(anomalies).map(([k, v]) => (
            <tr key={k}><td><code>{k}</code></td><td>{v.toLocaleString("fr-FR")}</td></tr>
          ))}
          {!Object.keys(anomalies).length && <tr><td colSpan={2}>Aucune anomalie</td></tr>}
        </tbody>
      </table>

      <h4 style={{ margin: "1rem 0 0.4rem" }}>Valeurs manquantes par colonne</h4>
      <table className="dt">
        <thead><tr><th>Colonne</th><th>Manquants</th></tr></thead>
        <tbody>
          {Object.entries(missing)
            .sort((a, b) => (b[1] || 0) - (a[1] || 0))
            .slice(0, 12)
            .map(([k, v]) => (
              <tr key={k}><td><code>{k}</code></td><td>{(v || 0).toLocaleString("fr-FR")}</td></tr>
            ))}
          {!Object.keys(missing).length && <tr><td colSpan={2}>Aucune valeur manquante</td></tr>}
        </tbody>
      </table>

      <h4 style={{ margin: "1rem 0 0.4rem" }}>Trous temporels ({gaps.length})</h4>
      <div className="dq-scroll">
        <table className="dt">
          <thead><tr><th>Capteur</th><th>Date</th><th>Interprétation</th></tr></thead>
          <tbody>
            {slice.map((g, i) => (
              <tr key={i}>
                <td><code>{g.sensor}</code></td>
                <td>{g.date}</td>
                <td>{g.interpretation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="pager">
        <button type="button" disabled={page <= 1} onClick={() => setPage(1)}>«</button>
        <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>‹</button>
        <input
          type="number"
          value={page}
          onChange={(e) => setPage(Math.max(1, parseInt(e.target.value) || 1))}
          aria-label="Numéro de page"
        />
        <span>sur {totalPages} pages</span>
        <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>›</button>
        <button type="button" disabled={page >= totalPages} onClick={() => setPage(totalPages)}>»</button>
      </div>
    </div>
  );
}
