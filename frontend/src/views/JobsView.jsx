/**
 * JobsView — jobs réels de l'API PyroLens (/api/v1/experiments).
 *
 * Chaque job = harmonisation, analyse FIRMS zone, historique archive ou
 * entraînement predict. Données réelles — aucun mock Slurm.
 *
 * Props: { onBack: () => void }
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { apiGet } from "../services/api.js";

const KIND_LABEL = {
  harmonization: "Harmonisation",
  firms_analyze: "Analyse zone FIRMS",
  firms_history: "Historique archive",
  predict: "Prédiction risque",
};

const STATUS_LABEL = {
  pending: "En attente",
  running: "En cours",
  succeeded: "Terminé",
  failed: "Échoué",
};

const PARAM_LABEL = {
  grid_deg: "Grille (°)",
  window: "Fenêtre (jours)",
  horizon_days: "Horizon (jours)",
  reference_date: "Date de référence",
  bbox: "Zone (bbox)",
  start: "Début",
  end: "Fin",
  years: "Années",
  countries: "Pays",
  sensors: "Capteurs",
  pair: "Paire capteurs",
  grid: "Grille",
  window_days: "Fenêtre (jours)",
};

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

function fmtParamValue(v) {
  if (v == null) return "—";
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

/** Paramètres lisibles ; le JSON brut reste disponible dans <details>. */
function JobParams({ params }) {
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
              <td style={{ width: "11rem" }}>{PARAM_LABEL[k] || k}</td>
              <td><code>{fmtParamValue(v)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <details>
        <summary style={{ cursor: "pointer", fontSize: "0.8rem", color: "var(--muted)" }}>
          Paramètres techniques (JSON)
        </summary>
        <code style={{ whiteSpace: "pre-wrap", fontSize: "0.78rem" }}>
          {JSON.stringify(params, null, 2)}
        </code>
      </details>
    </div>
  );
}

export default function JobsView({ onBack }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);   // vrai seulement au 1er fetch
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
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

  if (job) {
    const p = job.progress || {};
    return (
      <div className="content">
        <button className="btn-back" type="button" onClick={() => setSelectedId(null)}>
          ← Retour aux jobs
        </button>
        <div className="jtitle">
          <div>
            <h2>Job {job.job_id}</h2>
            <small>{KIND_LABEL[job.kind] || job.kind}</small>
          </div>
          <span className={`badge ${job.status === "succeeded" ? "COMPLETED" : job.status === "failed" ? "FAILED" : job.status === "running" ? "RUNNING" : "PENDING"}`}>
            {STATUS_LABEL[job.status] || job.status}
          </span>
        </div>
        <div className="jgrid">
          <div className="tl">
            {[
              ["Créé", fmtDate(job.created_at), "done"],
              ["Démarré", fmtDate(job.started_at), job.started_at ? "done" : "cur"],
              ["Progression", p.step ? `${p.step} — ${Math.round(p.pct || 0)}% ${p.detail || ""}` : "—", job.status === "running" ? "cur" : "done"],
              ["Terminé", fmtDate(job.finished_at), job.finished_at ? "done" : "pend"],
            ].map((s, i) => (
              <div key={i} className={`st ${s[2]}`}>
                <div className="c">
                  {s[2] === "done" && <span style={{ display: "grid", placeItems: "center" }}>✓</span>}
                </div>
                <div className="t">
                  <b>{s[0]}</b>
                  <span>{s[1]}</span>
                </div>
              </div>
            ))}
          </div>
          <table className="dt">
            <tbody>
              <tr><td>Type</td><td><code>{job.kind}</code></td></tr>
              <tr><td>Paramètres</td><td><JobParams params={job.params} /></td></tr>
              {job.error && <tr><td>Erreur</td><td><code style={{ whiteSpace: "pre-wrap" }}>{job.error}</code></td></tr>}
              {job.links?.result && (
                <tr><td>Résultat</td><td><code>{job.links.result}</code></td></tr>
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
          ← Retour à la carte
        </button>
      )}
      <h2>Jobs</h2>
      <small>
        Tâches réelles de l'API PyroLens : harmonisation, analyse de zone FIRMS,
        historique archive, entraînement du modèle de risque.
        {refreshing && " — actualisation…"}
      </small>
      {loading && <p className="empty">Chargement…</p>}
      {error && <div className="banner err">API indisponible : {error}</div>}
      {!loading && !error && items.length === 0 && (
        <p className="empty">Aucun job pour le moment — lance une analyse de zone ou une prédiction depuis la carte.</p>
      )}
      {items.length > 0 && (
        <table className="jl" style={{ marginTop: "1.4rem" }}>
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Type</th>
              <th>Statut</th>
              <th>Progression</th>
              <th>Créé le</th>
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
                  <td>{KIND_LABEL[j.kind] || j.kind}</td>
                  <td><span className={`badge ${badge}`}>{STATUS_LABEL[j.status] || j.status}</span></td>
                  <td>{j.progress?.step ? `${j.progress.step} ${Math.round(j.progress.pct || 0)}%` : "—"}</td>
                  <td>{fmtDate(j.created_at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
