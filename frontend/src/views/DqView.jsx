/**
 * DqView — vue Rapport de qualité des données (DQ).
 *
 * Props: { onClose: () => void }
 * Lit DQ_RULES depuis data/constants.js.
 */

import { useState, useEffect, useMemo } from "react";
import { buildDQRules, p2 } from "../data/constants.js";

const PAGE = 10;

export default function DqView({ onClose }) {
  const [rules, setRules] = useState([]);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [ent, setEnt] = useState("");
  const [dim, setDim] = useState("");
  const [col, setCol] = useState("");
  const [chips, setChips] = useState(new Set());
  const [sort, setSort] = useState(0);
  const [page, setPage] = useState(1);
  const [openRules, setOpenRules] = useState(new Set());

  useEffect(() => {
    setRules(buildDQRules());
  }, []);

  const cats = useMemo(() => [...new Set(rules.map((r) => r.cat))].sort(), [rules]);
  const ents = useMemo(() => [...new Set(rules.flatMap((r) => r.ents))].sort(), [rules]);
  const dims = useMemo(() => [...new Set(rules.map((r) => r.dim))].sort(), [rules]);
  const cols = useMemo(() => [...new Set(rules.map((r) => r.col))].sort(), [rules]);

  const filtered = useMemo(() => {
    let a = rules.filter((r) => {
      if (q && !r.col.toLowerCase().includes(q)) return false;
      if (cat && r.cat !== cat) return false;
      if (ent && !r.ents.includes(ent)) return false;
      if (dim && r.dim !== dim) return false;
      if (col && r.col !== col) return false;
      if (chips.size) {
        const k = typeof r.status === "number" ? "fail" : r.status;
        if (!chips.has(k)) return false;
      }
      return true;
    });
    if (sort) a = [...a].sort((x, y) => sort * (keyOf(y) - keyOf(x)));
    return a;
  }, [rules, q, cat, ent, dim, col, chips, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const slice = filtered.slice((page - 1) * PAGE, page * PAGE);

  function keyOf(r) {
    return typeof r.status === "number"
      ? r.status
      : r.status === "pass"
        ? 0
        : r.status === "err"
          ? -1
          : -2;
  }

  const toggleChip = (k) => {
    setChips((prev) => {
      const n = new Set(prev);
      n.has(k) ? n.delete(k) : n.add(k);
      return n;
    });
    setPage(1);
  };

  const toggleOpen = (id) => {
    setOpenRules((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  const exportCSV = () => {
    const header = "id,column,rule,dimension,status,severity\n";
    const rows = filtered
      .map(
        (r) =>
          `${r.id},${r.col},"${r.txt}",${r.dim},${typeof r.status === "number" ? r.status + "% failed" : r.status},${r.sev}`
      )
      .join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([header + rows], { type: "text/csv" }));
    a.download = "data_quality_report.csv";
    a.click();
  };

  return (
    <div className="dq-card">
      <div className="dq-top">
        <h3>Rapport de qualité des données</h3>
        <button className="ibtn" type="button" aria-label="Fermer le rapport" onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="dq-meta">
        Destination table – firms_hotspots (L2) | Execution ID – 1531 | Generated on{" "}
        {new Date().toLocaleString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
          hour: "numeric",
          minute: "2-digit",
        })}
      </div>

      <div className="dq-filters">
        <input
          id="dqQ"
          type="search"
          placeholder="Rechercher une colonne"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
        />
        <select value={cat} onChange={(e) => { setCat(e.target.value); setPage(1); }}>
          <option value="">Toutes les catégories</option>
          {cats.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={ent} onChange={(e) => { setEnt(e.target.value); setPage(1); }}>
          <option value="">Toutes les entités</option>
          {ents.map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
        <select value={dim} onChange={(e) => { setDim(e.target.value); setPage(1); }}>
          <option value="">Toutes les dimensions</option>
          {dims.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={col} onChange={(e) => { setCol(e.target.value); setPage(1); }}>
          <option value="">Toutes les colonnes</option>
          {cols.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <button className="dl" type="button" onClick={exportCSV}>
          ↓ CSV
        </button>
      </div>

      <div className="chips">
        {["fail", "pass", "none", "err"].map((k) => (
          <button
            key={k}
            type="button"
            className={`chip${chips.has(k) ? " on" : ""}`}
            aria-pressed={chips.has(k)}
            onClick={() => toggleChip(k)}
          >
            {k === "fail" && "⚠ En échec"}
            {k === "pass" && "✓ Réussies"}
            {k === "none" && "⊘ Non exécutées"}
            {k === "err" && "✗ Erreur d'exécution"}
          </button>
        ))}
      </div>

      <div className="dq-sum">
        {slice.length
          ? `${(page - 1) * PAGE + 1}–${(page - 1) * PAGE + slice.length} sur ${filtered.length} règles exécutées sur les hotspots`
          : "Aucune règle ne correspond aux filtres"}
      </div>

      <div className="dq-scroll">
        <table className="dq-t">
          <thead>
            <tr>
              <th>Colonne</th>
              <th>Règle</th>
              <th className="sortable" onClick={() => setSort((s) => (s === 1 ? -1 : 1))}>
                Statut {sort === 1 ? "↓" : sort === -1 ? "↑" : ""}
              </th>
              <th>Entités concernées</th>
              <th>Sév.</th>
              <th>Bypass</th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r) => (
              <>
                <tr key={r.id}>
                  <td>
                    <div className="col-cell">
                      <i>
                        {r.ty === "D" ? "📅" : r.ty === "N" ? "#" : "A"}
                      </i>
                      {r.col}
                      <span className="req" title="Colonne obligatoire">*</span>
                    </div>
                  </td>
                  <td>
                    <div className="rule-t">{r.txt}</div>
                    <div className="rule-m">{r.id} · {r.dim} · {r.scope}</div>
                  </td>
                  <td>{statusCell(r)}</td>
                  <td>{r.ents.map((e) => (
                    <span key={e} className={`tag ${["VIIRS", "MODIS", "GOES", "LANDSAT"].includes(e) ? "p" : ""}`}>{e}</span>
                  ))}</td>
                  <td>
                    <div className={`sev s${r.sev}`} title={`Sévérité ${r.sev}/3`}>
                      {r.sev > 1 ? "↑" : "↑"}
                    </div>
                  </td>
                  <td>
                    <div className="byp">
                      <button className="ch" type="button" onClick={() => toggleOpen(r.id)}>
                        {openRules.has(r.id) ? "↑" : "↓"}
                      </button>
                    </div>
                  </td>
                </tr>
                {openRules.has(r.id) && (
                  <tr className="det">
                    <td colSpan={6}>
                      <b>{r.id}</b> — colonne <b>{r.col}</b> · catégorie {r.cat} · dernière exécution{" "}
                      {new Date().toLocaleString("fr-FR")} · bypass : non
                    </td>
                  </tr>
                )}
              </>
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

function statusCell(r) {
  if (typeof r.status === "number")
    return (
      <div>
        <div className="bar" style={{ width: "8rem", height: ".5rem", overflow: "hidden", background: "#E1E9E5", borderRadius: "999px" }}>
          <b style={{ display: "block", height: "100%", width: `${r.status}%`, background: "var(--bad)" }} />
        </div>
        <div className="stat-fail">{r.status}% d&apos;enregistrements en échec</div>
      </div>
    );
  if (r.status === "pass")
    return <span className="ok">✓ Conforme</span>;
  if (r.status === "err")
    return <span className="stat-err">⚠ Erreur d&apos;exécution</span>;
  return <span className="stat-none">⊘ Non exécutée</span>;
}
