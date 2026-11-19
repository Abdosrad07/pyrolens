/**
 * JobsView — jobs réels de l'API PyroLens (/api/v1/experiments).
 *
 * Props: { onBack: () => void }
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { apiGet } from "../services/api.js";
import { useI18n } from "../i18n/index.jsx";

const PARAM_KEYS = [
  "grid_deg", "window", "horizon_days", "reference_date", "bbox", "start",
  "end", "years", "countries", "sensors", "pair", "grid", "window_days", "source",
];

function fmtParamValue(v) {
  if (v == null) return "—";
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

/** Paramètres lisibles ; le JSON brut reste disponible dans <details>. */
function JobParams({ params, t }) {
  if (!params || typeof params !== "object" || !Object.keys(params).length) {
    return <span>—</span>;
  }
  const entries = Object.entries(params);
  return (
    <div>
      <table className="dt" style={{ marginBottom: "0.4rem" }}>
        <tbody>
          {entries.map(([k, v]) => (
            <tr key={k}>
              <td style={{ width: "11rem" }}>{PARAM_KEYS.includes(k) ? t(`jobs.param.${k}`, k) : k}</td>
              <td><code>{fmtParamValue(v)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <details>
        <summary style={{ cursor: "pointer", fontSize: "0.8rem", color: "var(--muted)" }}>
          {t("jobs.table.rawParams", "Technical parameters (JSON)")}
        </summary>
        <code style={{ whiteSpace: "pre-wrap", fontSize: "0.78rem" }}>
          {JSON.stringify(params, null, 2)}
        </code>
      </details>
    </div>
  );
}

/** Section d'explication de l'harmonisation — s'affiche en haut de la vue. */
function HarmonizationExplainer() {
  const { t } = useI18n();
  return (
    <div style={{
      margin: "0.8rem 0 1.4rem",
      padding: "1rem",
      background: "rgba(240,130,50,0.04)",
      borderLeft: "3px solid #f08232",
      borderRadius: "0 0.4rem 0.4rem 0",
      fontSize: "0.85rem",
      lineHeight: 1.5,
    }}>
      <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem", fontWeight: 600 }}>
        {t("jobs.harmTitle", "Comment fonctionne l'harmonisation ?")}
      </h3>
      <p style={{ margin: "0 0 0.6rem", opacity: 0.85 }}>
        {t("jobs.harmDesc", "PyroLens compare les détections de deux capteurs (VIIRS et MODIS) sur une grille commune de 0,25°. Pour chaque cellule et chaque fenêtre temporelle, le système calcule :")}
      </p>
      <ol style={{ margin: "0 0 0.6rem", paddingLeft: "1.4rem", opacity: 0.85, fontSize: "0.82rem" }}>
        <li style={{ marginBottom: "0.3rem" }}>
          <strong>{t("jobs.harmStep1", "Normalisation")}</strong> — Les CSV bruts FIRMS (colonne « satellite ») sont séparés en sous-ensembles par capteur (Terra, Aqua, VIIRS SNPP).
        </li>
        <li style={{ marginBottom: "0.3rem" }}>
          <strong>{t("jobs.harmStep2", "Grille commune")}</strong> — Chaque détection est projetée sur une maille 0,25° × 0,25° (cellule = i, j). Les fenêtres de 1, 4, 8 ou 16 jours regroupent les détections.
        </li>
        <li style={{ marginBottom: "0.3rem" }}>
          <strong>{t("jobs.harmStep3", "Comparaison d'ensembles")}</strong> — L'intersection, l'union et le coefficient de Jaccard (|A∩B| / |A∪B|) sont calculés par configuration (paire × grille × fenêtre).
        </li>
        <li style={{ marginBottom: "0.3rem" }}>
          <strong>{t("jobs.harmStep4", "Séries mensuelles")}</strong> — La divergence est agrégée par mois, par jour et par région (tercile de latitude) pour identifier les zones de désaccord.
        </li>
      </ol>
      <p style={{ margin: 0, opacity: 0.6, fontSize: "0.78rem" }}>
        {t("jobs.harmNote", "Note : le Jaccard mesure un recouvrement d'ensembles, pas une précision. Aucune référence indépendante n'est mobilisée (H4/H6 non exécutés).")}
      </p>
    </div>
  );
}

export default function JobsView({ onBack }) {
  const { t, lang } = useI18n();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);   // vrai seulement au 1er fetch
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [showExplainer, setShowExplainer] = useState(true);
  const firstLoad = useRef(true);

  // apiGet est une fonction module stable : load/intervalle ne changent jamais.
  const load = useCallback(async () => {
    if (firstLoad.current) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const j = await apiGet("/api/v1/experiments");
      setItems(j.items || []);
    } catch (e) {
      setError(e.message);
      if (firstLoad.current) setItems([]);
    } finally {
      firstLoad.current = false;
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 8000); // polling silencieux : pas de flash visuel
    return () => clearInterval(t);
  }, [load]);

  const job = items.find((j) => j.job_id === selectedId);

  const fmtDateLoc = (iso) => {
    if (!iso) return "—";
    const loc = lang === "en" ? "en-US" : "fr-FR";
    return new Date(iso).toLocaleString(loc, { dateStyle: "short", timeStyle: "short" });
  };

  if (job) {
    const p = job.progress || {};
    return (
      <div className="content">
        <button className="btn-back" type="button" onClick={() => setSelectedId(null)}>
          {t("jobs.back")}
        </button>
        <div className="jtitle">
          <div>
            <h2>Job {job.job_id}</h2>
            <small>{t(`jobs.kind.${job.kind}`, job.kind)}</small>
          </div>
          <span className={`badge ${job.status === "succeeded" ? "COMPLETED" : job.status === "failed" ? "FAILED" : job.status === "running" ? "RUNNING" : "PENDING"}`}>
            {t(`jobs.status.${job.status}`, job.status)}
          </span>
        </div>
        <div className="jgrid">
          <div className="tl">
            {[
              ["created", fmtDateLoc(job.created_at), "done"],
              ["started", fmtDateLoc(job.started_at), job.started_at ? "done" : "cur"],
              ["progress", p.step ? `${p.step} — ${Math.round(p.pct || 0)}% ${p.detail || ""}` : "—", job.status === "running" ? "cur" : "done"],
              ["finished", fmtDateLoc(job.finished_at), job.finished_at ? "done" : "pend"],
            ].map((s, i) => (
              <div key={i} className={`st ${s[2]}`}>
                <div className="c">
                  {s[2] === "done" && <span style={{ display: "grid", placeItems: "center" }}>✓</span>}
                </div>
                <div className="t">
                  <b>{t(`jobs.timeline.${s[0]}`, s[0])}</b>
                  <span>{s[1]}</span>
                </div>
              </div>
            ))}
          </div>
          <table className="dt">
            <tbody>
              <tr><td>{t("jobs.table.type", "Type")}</td><td><code>{job.kind}</code></td></tr>
              <tr><td>{t("jobs.table.params", "Paramètres")}</td><td><JobParams params={job.params} t={t} /></td></tr>
              {job.error && <tr><td>{t("jobs.table.error", "Erreur")}</td><td><code style={{ whiteSpace: "pre-wrap" }}>{job.error}</code></td></tr>}
              {job.links?.result && (
                <tr><td>{t("jobs.table.result")}</td><td><code>{job.links.result}</code></td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="content">
      {onBack && (
        <button className="btn-back" type="button" onClick={onBack} style={{ marginBottom: "0.8rem" }}>
          {t("common.backToMap", "← Retour à la carte")}
        </button>
      )}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
        <h2>{t("jobs.title")}</h2>
        <button
          type="button"
          onClick={() => setShowExplainer((v) => !v)}
          style={{
            background: "none",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: "0.4rem",
            color: "rgba(255,255,255,0.7)",
            cursor: "pointer",
            fontSize: "0.78rem",
            padding: "0.3rem 0.7rem",
          }}
        >
          {showExplainer ? "▲ " : "▼ "}{t("jobs.harmToggle", "Procédé d'harmonisation")}
        </button>
      </div>
      <small>{t("jobs.subtitle")}</small>

      {showExplainer && <HarmonizationExplainer />}

      {loading && <p className="empty">{t("jobs.loading")}</p>}
      {error && <div className="banner err">{t("jobs.apiError")} {error}</div>}
      {!loading && !error && items.length === 0 && (
        <p className="empty">{t("jobs.none")}</p>
      )}
      {items.length > 0 && (
        <table className="jl" style={{ marginTop: "1rem" }}>
          <thead>
            <tr>
              <th>{t("jobs.headers.jobId")}</th>
              <th>{t("jobs.headers.type")}</th>
              <th>{t("jobs.headers.status")}</th>
              <th>{t("jobs.headers.progress")}</th>
              <th>{t("jobs.headers.created")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((j) => {
              const badge =
                j.status === "succeeded" ? "COMPLETED" :
                j.status === "failed" ? "FAILED" :
                j.status === "running" ? "RUNNING" : "PENDING";
              return (
                <tr
                  key={j.job_id}
                  tabIndex={0}
                  aria-label={`Ouvrir le job ${j.job_id}`}
                  onClick={() => setSelectedId(j.job_id)}
                  onKeyDown={(e) => { if (e.key === "Enter") setSelectedId(j.job_id); }}
                >
                  <td><code>{j.job_id}</code></td>
                  <td>{t(`jobs.kind.${j.kind}`, j.kind)}</td>
                  <td><span className={`badge ${badge}`}>{t(`jobs.status.${j.status}`, j.status)}</span></td>
                  <td>{j.progress?.step ? `${j.progress.step} ${Math.round(j.progress.pct || 0)}%` : "—"}</td>
                  <td>{fmtDateLoc(j.created_at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
