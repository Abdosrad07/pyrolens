/**
 * CalendarView — calendrier réel du pipeline (/api/v1/fire-calendar/daily).
 *
 * Chaque jour = comptage de cellules en divergence inter-capteurs
 * (a_only + b_only). Niveau = terciles des jours non nuls — jamais de
 * "pas de feu" : un jour vide signifie seulement aucune divergence mesurée.
 */

import { useState, useEffect, useMemo } from "react";
import useApi from "../hooks/useApi.js";

const MONTHS_FR = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];
const DOW = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

function levelOf(total, t1, t2) {
  if (total >= t2) return "critical";
  if (total >= t1) return "high";
  return "medium";
}

export default function CalendarView({ onBack }) {
  const { fireCalendarDaily } = useApi(); // callback stable (useCallback [])
  const today = new Date();
  const [year, setYear] = useState(2020); // données pipeline : 2013–2020
  const [month, setMonth] = useState(11);
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    fireCalendarDaily({ limit: 20000 })
      .then((j) => { if (alive) setRows(j.rows || []); })
      .catch((e) => { if (alive) setError(e.message); });
    return () => { alive = false; };
  }, [fireCalendarDaily]);

  // date → total (somme des paires du jour)
  const byDay = useMemo(() => {
    const m = new Map();
    for (const r of rows || []) {
      m.set(r.date, (m.get(r.date) || 0) + (r.total || 0));
    }
    return m;
  }, [rows]);

  // terciles des jours non nuls → seuils de niveau
  const { t1, t2 } = useMemo(() => {
    const vals = [...byDay.values()].filter((v) => v > 0).sort((a, b) => a - b);
    if (!vals.length) return { t1: 1, t2: 2 };
    return {
      t1: vals[Math.floor(vals.length / 3)] || 1,
      t2: vals[Math.floor((2 * vals.length) / 3)] || 2,
    };
  }, [byDay]);

  const firstDay = new Date(year, month, 1);
  const startWeekday = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const p2 = (n) => String(n).padStart(2, "0");
  const iso = (d) => `${year}-${p2(month + 1)}-${p2(d)}`;

  return (
    <div className="content">
      {onBack && (
        <button className="btn-back" type="button" onClick={onBack} style={{ marginBottom: "0.8rem" }}>
          ← Retour à la carte
        </button>
      )}
      <h2>Calendrier des feux</h2>
      <small>
        Données réelles du pipeline PyroLens (2013–2020) : cellules en divergence
        inter-capteurs par jour. Un jour sans marqueur = aucune divergence mesurée,
        pas « absence de feu ».
      </small>
      {error && <div className="banner err">API indisponible : {error}</div>}
      {!rows && !error && <p className="empty">Chargement du calendrier…</p>}
      <div className="cal-nav">
        <button type="button" className="ibtn" onClick={() => {
          if (month === 0) { setMonth(11); setYear(year - 1); }
          else setMonth(month - 1);
        }}>
          ←
        </button>
        <h3>{MONTHS_FR[month]} {year}</h3>
        <button type="button" className="ibtn" onClick={() => {
          if (month === 11) { setMonth(0); setYear(year + 1); }
          else setMonth(month + 1);
        }}>
          →
        </button>
      </div>
      <div className="cal-grid">
        {DOW.map((d) => (
          <div key={d} className="cal-dow">{d}</div>
        ))}
        {cells.map((d, i) => {
          const date = d ? iso(d) : null;
          const total = date ? byDay.get(date) || 0 : 0;
          const lvl = total > 0 ? levelOf(total, t1, t2) : null;
          const isToday = date && date === today.toISOString().slice(0, 10);
          return (
            <div
              key={i}
              className={`cal-cell${lvl ? ` fire-${lvl}` : ""}${isToday ? " on" : ""}`}
              aria-disabled={!d}
              title={total > 0 ? `${date} : ${total} cellules en divergence` : undefined}
            >
              {d && <strong>{d}</strong>}
              {lvl && <span style={{ fontSize: "0.6rem", color: "var(--ember)" }}>{total}</span>}
            </div>
          );
        })}
      </div>
      <div className="banner info" style={{ marginTop: "1rem" }}>
        <b>Légende</b> · nombre = cellules en divergence capteurs ce jour-là ·
        niveaux = terciles des jours non nuls
        {rows && <> · {rows.length} jours couverts</>}
      </div>
    </div>
  );
}
