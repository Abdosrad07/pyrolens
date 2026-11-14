/**
 * CalendarView — vue Calendrier des feux (mock).
 */

import { useState } from "react";

const MONTHS_FR = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];

const DOW = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

export default function CalendarView() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth()); // 0-11

  const firstDay = new Date(year, month, 1);
  const startWeekday = (firstDay.getDay() + 6) % 7; // lundi = 0
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Jours simulés avec "feu"
  function hasFire(d) {
    const seed = d.getDate() * 7 + d.getMonth() * 31 + year;
    return seed % 5 === 0;
  }
  function fireLevel(d) {
    const seed = d.getDate() * 7 + d.getMonth() * 31 + year;
    const v = seed % 10;
    if (v >= 8) return "critical";
    if (v >= 5) return "high";
    if (v >= 2) return "medium";
    return "low";
  }

  const cells = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <div className="content">
      <h2>Calendrier des feux</h2>
      <small>
        Vue mensuelle synthétique des alertes feu détectées par les satellites NASA FIRMS.
      </small>
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
          const date = d ? new Date(year, month, d) : null;
          const fire = date ? hasFire(date) : false;
          const lvl = date && fire ? fireLevel(date) : null;
          const isToday = date && date.toDateString() === today.toDateString();
          return (
            <div
              key={i}
              className={`cal-cell${fire ? ` fire-${lvl}` : ""}${isToday ? " on" : ""}`}
              aria-disabled={!d}
            >
              {d && <strong>{d}</strong>}
              {fire && <span style={{ fontSize: "0.6rem", color: "var(--ember)" }}>🔥 {lvl === "critical" ? "!" : ""}</span>}
            </div>
          );
        })}
      </div>
      <div className="banner info" style={{ marginTop: "1rem" }}>
        <b>Légende</b> · 🔥 Faible / 🟠 Élevé / 🔴 Critique
      </div>
    </div>
  );
}
