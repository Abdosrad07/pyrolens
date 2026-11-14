/**
 * JobsView — vue Jobs de traitement (type Slurm-web).
 *
 * Props: { onBack: () => void }
 */

import { useState, useEffect } from "react";
import { JOBS, fdt, NOW0 } from "../data/constants.js";

export default function JobsView({ onBack }) {
  const [selectedId, setSelectedId] = useState(null);
  const [timer, setTimer] = useState(null);

  const job = JOBS.find((j) => j.id === selectedId);

  const stepsFor = (j) => {
    const sub = (j.start ?? NOW0) - 175e3;
    const st = j.start;
    const p2 = (n) => String(n).padStart(2, "0");
    const fmt = (ms) => {
      const d = new Date(ms);
      return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()} ${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())}`;
    };
    if (j.state === "RUNNING")
      return [
        ["Submitted", fmt(sub), "done"],
        ["Eligible", fmt(sub), "done"],
        ["Scheduling", fmt(st), "done"],
        ["Running", <span key="e">{j.elapsed} seconds elapsed</span>, "cur"],
        ["Completing", `Limite ${fmt(st + j.limit * 60e3)}`, "pend"],
        ["Terminated", "", "pend"],
      ];
    if (j.state === "COMPLETED")
      return [
        ["Submitted", fmt(sub), "done"],
        ["Eligible", fmt(sub), "done"],
        ["Scheduling", fmt(st), "done"],
        ["Running", `${j.elapsed} seconds`, "done"],
        ["Completing", fmt(st + j.elapsed * 1e3), "done"],
        ["Terminated", fmt(st + j.elapsed * 1e3 + 4e3), "done"],
      ];
    if (j.state === "FAILED")
      return [
        ["Submitted", fmt(sub), "done"],
        ["Eligible", fmt(sub), "done"],
        ["Scheduling", fmt(st), "done"],
        ["Running", `${j.elapsed} seconds`, "done"],
        ["Completing", fmt(st + j.elapsed * 1e3), "done"],
        ["Terminated", `Échec – ${fmt(st + j.elapsed * 1e3 + 3e3)}`, "done"],
      ];
    return [
      ["Submitted", fmt(sub), "done"],
      ["Eligible", fmt(sub), "done"],
      ["Scheduling", "En attente de ressources", "cur"],
      ["Running", "", "pend"],
      ["Completing", "", "pend"],
      ["Terminated", "", "pend"],
    ];
  };

  useEffect(() => {
    if (job?.state === "RUNNING") {
      const t0 = Date.now();
      setTimer(
        setInterval(() => {
          setSelectedId((id) => {
            const j = JOBS.find((x) => x.id === id);
            if (j?.state !== "RUNNING") return id;
            return id;
          });
        }, 1000)
      );
    }
    return () => clearInterval(timer);
  }, [job?.state]);

  if (job) {
    const rows = [
      ["User", j.user],
      ["Group", "scientists"],
      ["Account", "fire-monitoring"],
      ["Wckeys", ""],
      ["Priority", j.prio],
      ["Name", j.name],
      ["Comments", ""],
      ["Submit line", j.cmd],
      ["Script", ""],
      ["Working directory", `/home/${j.user}`],
      ["Exit Code", j.exit],
      ["Nodes", j.nodes],
      ["Partition", j.part],
      ["QOS", j.state === "FAILED" ? "low" : "normal"],
      ["Requested", `Nodes : 1\nCPU : 1\nMemory : 512 MB${j.gpu ? "\nGPU : h100 × 4" : ""}`],
    ];
    return (
      <div className="content">
        <button className="btn-back" type="button" onClick={onBack}>
          ← Retour aux jobs
        </button>
        <div className="jtitle">
          <div>
            <h2>Job {job.id}</h2>
            <small>All job settings</small>
          </div>
          <span className={`badge ${job.state}`}>{job.state}</span>
        </div>
        <div className="jgrid">
          <div className="tl">
            {stepsFor(job).map((s, i) => (
              <div key={i} className={`st ${s[2]}`}>
                <div className="c">
                  {s[2] === "done" && <span style={{ display: "grid", placeItems: "center" }}>✓</span>}
                </div>
                <div className="t">
                  <b>{s[0]}</b>
                  <span>{typeof s[1] === "string" ? s[1] : s[1]}</span>
                </div>
              </div>
            ))}
          </div>
          <table className="dt">
            <tbody>
              {rows.map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{v === "" ? "" : <code style={{ whiteSpace: "pre-wrap" }}>{v}</code>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="content">
      <h2>Jobs</h2>
      <small>
        Traitements de données incendie (ingestion VIIRS/MODIS, détection de clusters, exports FRP)
      </small>
      <table className="jl" style={{ marginTop: "1.4rem" }}>
        <thead>
          <tr>
            <th>Job ID</th>
            <th>Nom</th>
            <th>Utilisateur</th>
            <th>Partition</th>
            <th>Priorité</th>
            <th>État</th>
          </tr>
        </thead>
        <tbody>
          {JOBS.map((j) => (
            <tr
              key={j.id}
              tabIndex={0}
              aria-label={`Ouvrir le job ${j.id}`}
              onClick={() => setSelectedId(j.id)}
              onKeyDown={(e) => { if (e.key === "Enter") setSelectedId(j.id); }}
            >
              <td>{j.id}</td>
              <td>{j.name}</td>
              <td>{j.user}</td>
              <td>{j.part}</td>
              <td>{j.prio}</td>
              <td><span className={`badge ${j.state}`}>{j.state}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
