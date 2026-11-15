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
  const { t, lang } = useI18n();
  const loc = lang === "en" ? "en-US" : "fr-FR";
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
        <div className="banner err">{t("dq.artifactError", "audit.json artifact unavailable:")} {error}</div>
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
        <h3>{t("dq.title", "Data quality report")}</h3>
        <button className="ibtn" type="button" aria-label={t("dq.close", "Close report")} onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="dq-meta">
        {t("dq.meta", "{n} files · origin {origin} · generated {date}", {
          n: Number(audit.n_files).toLocaleString(loc),
          origin: audit.data_origin,
          date: audit.generated_at ? new Date(audit.generated_at).toLocaleString(loc) : "?",
        })}
      </div>

      {audit.interpretation_warning && (
        <div className="banner warn" style={{ margin: "0.8rem 0" }}>
          {t("dq.warning", audit.interpretation_warning)}
        </div>
      )}

      <div className="cards" style={{ margin: "1rem 0" }}>
        <div className="card">
          <div className="k">{t("dq.cards.files", "Files audited")}</div>
          <div className="v">{audit.n_files}</div>
          <div className="u">{audit.data_origin}</div>
        </div>
        <div className="card">
          <div className="k">{t("dq.cards.anomalies", "Anomalies")}</div>
          <div className="v">{Object.values(anomalies).reduce((a, b) => a + b, 0).toLocaleString(loc)}</div>
          <div className="u">{Object.keys(anomalies).join(", ") || t("dq.noneAnomaly", "none")}</div>
        </div>
        <div className="card">
          <div className="k">{t("dq.cards.rows", "Classified rows")}</div>
          <div className="v">{Object.entries(classes).map(([k, v]) => `${k}: ${v.toLocaleString(loc)}`).join(" · ") || "—"}</div>
          <div className="u">{t("dq.cards.rowsUnit", "rigorous classification")}</div>
        </div>
        <div className="card">
          <div className="k">{t("dq.cards.gaps", "Days without records")}</div>
          <div className="v">{audit.temporal_gaps?.n_entries ?? 0}</div>
          <div className="u">{t("dq.cards.gapsUnit", "sensor temporal gaps")}</div>
        </div>
      </div>

      <h4 style={{ margin: "1rem 0 0.4rem" }}>{t("dq.sections.anomalies", "Anomalies by category")}</h4>
      <table className="dt">
        <thead><tr><th>{t("dq.th.category", "Category")}</th><th>{t("dq.th.count", "Count")}</th></tr></thead>
        <tbody>
          {Object.entries(anomalies).map(([k, v]) => (
            <tr key={k}><td><code>{k}</code></td><td>{v.toLocaleString(loc)}</td></tr>
          ))}
          {!Object.keys(anomalies).length && <tr><td colSpan={2}>{t("dq.noneAnomaly", "No anomalies")}</td></tr>}
        </tbody>
      </table>

      <h4 style={{ margin: "1rem 0 0.4rem" }}>{t("dq.sections.missing", "Missing values by column")}</h4>
      <table className="dt">
        <thead><tr><th>{t("dq.th.column", "Column")}</th><th>{t("dq.th.missing", "Missing")}</th></tr></thead>
        <tbody>
          {Object.entries(missing)
            .sort((a, b) => (b[1] || 0) - (a[1] || 0))
            .slice(0, 12)
            .map(([k, v]) => (
              <tr key={k}><td><code>{k}</code></td><td>{(v || 0).toLocaleString(loc)}</td></tr>
            ))}
          {!Object.keys(missing).length && <tr><td colSpan={2}>{t("dq.noneMissing", "No missing values")}</td></tr>}
        </tbody>
      </table>

      <h4 style={{ margin: "1rem 0 0.4rem" }}>{t("dq.sections.gaps", "Temporal gaps ({n})", { n: gaps.length })}</h4>
      <div className="dq-scroll">
        <table className="dt">
          <thead><tr><th>{t("dq.th.sensor", "Sensor")}</th><th>{t("dq.th.date", "Date")}</th><th>{t("dq.th.interpretation", "Interpretation")}</th></tr></thead>
          <tbody>
            {slice.map((g, i) => (
              <tr key={i}>
                <td><code>{g.sensor}</code></td>
                <td>{g.date}</td>
                <td>{t(`dq.interp.${g.interpretation}`, g.interpretation)}</td>
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
          aria-label={t("dq.pageLabel", "Page number")}
        />
        <span>{t("dq.pageOf", "of {n} pages", { n: totalPages })}</span>
        <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>›</button>
        <button type="button" disabled={page >= totalPages} onClick={() => setPage(totalPages)}>»</button>
      </div>
    </div>
  );
}
