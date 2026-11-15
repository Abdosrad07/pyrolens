/**
 * JobsView — jobs réels de l'API PyroLens (/api/v1/experiments).
 *
 * Props: { onBack: () => void }
 */

import { useState, useEffect, useCallback } from "react";
import { useI18n } from "../i18n/index.jsx";
import useApi from "../hooks/useApi.js";

export default function JobsView({ onBack }) {
  const { t } = useI18n();
  const api = useApi();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const j = await api.listJobs();
      setItems(j.items || []);
    } catch (e) {
      setError(e.message);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    load();
    const t2 = setInterval(load, 8000);
    return () => clearInterval(t2);
  }, [load]);

  const job = items.find((j) => j.job_id === selectedId);

  function fmtDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    const loc = t("lang.fr") === "Français" ? "fr-FR" : "en-US";
    return d.toLocaleString(loc, { dateStyle: "short", timeStyle: "short" });
  }

  const TL = (s) => s[0] ? t(`jobs.timeline.${s[0]}`, s[0]) : "";
  const SK = (s) => s[0] ? t(`jobs.kind.${s[0]}`, s[0]) : "";

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
              ["created", fmtDate(job.created_at), "done"],
              ["started", fmtDate(job.started_at), job.started_at ? "done" : "cur"],
              ["progress", p.step ? `${p.step} — ${Math.round(p.pct || 0)}% ${p.detail || ""}` : "—", job.status === "running" ? "cur" : "done"],
              ["finished", fmtDate(job.finished_at), job.finished_at ? "done" : "pend"],
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
              <tr><td>{t("jobs.table.type")}</td><td><code>{job.kind}</code></td></tr>
              <tr><td>{t("jobs.table.params")}</td><td><code style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(job.params, null, 2)}</code></td></tr>
              {job.error && <tr><td>{t("jobs.table.error")}</td><td><code style={{ whiteSpace: "pre-wrap" }}>{job.error}</code></td></tr>}
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
      <h2>{t("jobs.title")}</h2>
      <small>{t("jobs.subtitle")}</small>
      {loading && <p className="empty">{t("jobs.loading")}</p>}
      {error && <div className="banner err">{t("jobs.apiError")} {error}</div>}
      {!loading && !error && items.length === 0 && (
        <p className="empty">{t("jobs.none")}</p>
      )}
      {items.length > 0 && (
        <table className="jl" style={{ marginTop: "1.4rem" }}>
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
