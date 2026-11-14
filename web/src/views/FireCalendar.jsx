/**
 * FireCalendar - Calendrier des feux et séries temporelles.
 * Données : loadFireCalendar() (API /fire-calendar/* ou baselines.json en statique).
 * Aucun état n'affirme une absence de feu : les jours sans enregistrement
 * sont simplement vides (« aucun enregistrement », jamais « pas de feu »).
 */
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatCard from "../components/StatCard.jsx";
import LoadingState from "../components/LoadingState.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import DateRangeFilter from "../components/DateRangeFilter.jsx";
import { fmt, loadFireCalendar, pairLabel } from "../data.js";

const PAIR_COLORS = {
  terra__aqua: "#ff7a33",
  aqua__viirs_snpp: "#35c8c0",
  terra_viirs_snpp: "#5aa7ff",
};

const WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"];
const GRANULARITIES = [
  { id: "day", label: "Jour" },
  { id: "week", label: "Semaine" },
  { id: "month", label: "Mois" },
];

// ---------- helpers ---------------------------------------------------------

function isoWeekKey(dateStr) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const dayNum = (t.getUTCDay() + 6) % 7; // lundi = 0
  t.setUTCDate(t.getUTCDate() - dayNum + 3); // jeudi de la semaine ISO
  const firstThursday = new Date(Date.UTC(t.getUTCFullYear(), 0, 4));
  const fd = (firstThursday.getUTCDay() + 6) % 7;
  firstThursday.setUTCDate(firstThursday.getUTCDate() - fd + 3);
  const week = 1 + Math.round((t - firstThursday) / (7 * 86400000));
  return `${t.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

const zero = () => ({ a_only: 0, b_only: 0, both: 0, total: 0 });

function addInto(acc, r) {
  acc.a_only += r.a_only || 0;
  acc.b_only += r.b_only || 0;
  acc.both += r.both || 0;
  acc.total += r.total ?? (r.a_only || 0) + (r.b_only || 0);
}

function aggregate(rows, keyOf) {
  const map = new Map();
  for (const r of rows) {
    const k = keyOf(r);
    if (!map.has(k)) map.set(k, zero());
    addInto(map.get(k), r);
  }
  return [...map.entries()]
    .map(([period, s]) => ({ period, ...s }))
    .sort((a, b) => (a.period < b.period ? -1 : 1));
}

function monthKey(dateStr) {
  return dateStr.slice(0, 7);
}

// ---------- vue ----------------------------------------------------------------

export default function FireCalendar() {
  const [fc, setFc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [pair, setPair] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [granularity, setGranularity] = useState("month");
  const [calCursor, setCalCursor] = useState(() => {
    const d = new Date();
    return { y: d.getUTCFullYear(), m: d.getUTCMonth() };
  });
  const [selected, setSelected] = useState(null); // { label, stats, jaccard? }

  useEffect(() => {
    let alive = true;
    loadFireCalendar()
      .then((result) => {
        if (!alive) return;
        setFc(result);
        setLoading(false);
        if (!startDate && result.daily?.length) {
          const dates = result.daily.map((r) => r.date).sort();
          setStartDate(dates[0]);
          setEndDate(dates[dates.length - 1]);
        }
      })
      .catch((err) => {
        if (alive) {
          setError(err);
          setLoading(false);
        }
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pairs = useMemo(
    () => [...new Set((fc?.daily || []).map((r) => r.pair))],
    [fc]
  );

  // ---------- filtrage ----------
  const inPair = (r) => pair === "all" || r.pair === pair;
  const inRange = (period, isDay) => {
    if (!startDate && !endDate) return true;
    if (isDay) {
      if (startDate && period < startDate) return false;
      if (endDate && period > endDate) return false;
      return true;
    }
    const m = period.slice(0, 7);
    if (startDate && m < startDate.slice(0, 7)) return false;
    if (endDate && m > endDate.slice(0, 7)) return false;
    return true;
  };

  const daily = useMemo(
    () =>
      (fc?.daily || [])
        .filter((r) => inPair(r) && inRange(r.date, true))
        .sort((a, b) => (a.date < b.date ? -1 : 1)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fc, pair, startDate, endDate]
  );
  const monthly = useMemo(
    () =>
      (fc?.monthly || [])
        .filter((r) => inPair(r) && inRange(r.month, false))
        .sort((a, b) => (a.month < b.month ? -1 : 1)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fc, pair, startDate, endDate]
  );
  const jaccard = useMemo(
    () =>
      (fc?.jaccard || []).filter(
        (r) => inPair(r) && inRange(r.month, false)
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fc, pair, startDate, endDate]
  );

  // ---------- agrégations pour les graphiques ----------
  const series = useMemo(() => {
    if (granularity === "month") {
      const map = new Map();
      for (const r of monthly) {
        const cur = map.get(r.month) || zero();
        addInto(cur, r);
        map.set(r.month, cur);
      }
      return [...map.entries()]
        .map(([period, s]) => ({ period, ...s }))
        .sort((a, b) => (a.period < b.period ? -1 : 1));
    }
    const keyOf = granularity === "week" ? (r) => isoWeekKey(r.date) : (r) => r.date;
    return aggregate(daily, keyOf);
  }, [granularity, daily, monthly]);

  const byDay = useMemo(() => {
    const map = new Map();
    for (const r of daily) {
      const cur = map.get(r.date) || zero();
      addInto(cur, r);
      map.set(r.date, cur);
    }
    return map;
  }, [daily]);

  const jaccardByMonth = useMemo(() => {
    const map = new Map(); // month -> { period, <pair>: jaccard }
    for (const r of jaccard) {
      const cur = map.get(r.month) || { period: r.month };
      cur[r.pair] = r.jaccard;
      map.set(r.month, cur);
    }
    return [...map.values()].sort((a, b) => (a.period < b.period ? -1 : 1));
  }, [jaccard]);

  // ---------- statistiques ----------
  const stats = useMemo(() => {
    const daysWithData = byDay.size;
    let peak = 0;
    let sum = 0;
    for (const s of byDay.values()) {
      sum += s.total;
      if (s.total > peak) peak = s.total;
    }
    const jVals = jaccard.map((r) => r.jaccard).filter((v) => v != null);
    const jMean = jVals.length
      ? jVals.reduce((a, b) => a + b, 0) / jVals.length
      : null;
    return { daysWithData, peak, sum, jMean };
  }, [byDay, jaccard]);

  // ---------- calendrier ----------
  const calDays = useMemo(() => {
    const { y, m } = calCursor;
    const firstWeekday = (new Date(Date.UTC(y, m, 1)).getUTCDay() + 6) % 7;
    const nDays = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    const cells = [];
    for (let i = 0; i < firstWeekday; i++) cells.push(null);
    for (let d = 1; d <= nDays; d++) {
      const iso = `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      cells.push({ iso, day: d, stats: byDay.get(iso) || null });
    }
    return cells;
  }, [calCursor, byDay]);

  const maxDayTotal = useMemo(() => {
    let max = 0;
    for (const s of byDay.values()) if (s.total > max) max = s.total;
    return max || 1;
  }, [byDay]);

  function shiftMonth(delta) {
    setCalCursor(({ y, m }) => {
      const d = new Date(Date.UTC(y, m + delta, 1));
      return { y: d.getUTCFullYear(), m: d.getUTCMonth() };
    });
  }

  function selectPeriod(period, kind) {
    let stats = null;
    let j = [];
    if (kind === "day") {
      stats = byDay.get(period) || zero();
    } else if (kind === "week") {
      stats = aggregate(daily, (r) => isoWeekKey(r.date)).find(
        (s) => s.period === period
      );
    } else {
      stats = aggregate(monthly, (r) => r.month).find((s) => s.period === period);
      const jr = jaccardByMonth.find((s) => s.period === period);
      j = jr
        ? pairs.filter((p) => jr[p] != null).map((p) => ({ pair: p, value: jr[p] }))
        : [];
    }
    setSelected({
      label: period,
      kind,
      stats: stats || zero(),
      jaccards: j,
    });
  }

  function onBarClick(d) {
    const p = d?.payload || d;
    if (p?.period) selectPeriod(p.period, granularity);
  }

  // Point cliquable pour le LineChart mensuel (détail période au clic).
  function monthDot(props) {
    const { cx, cy, payload, stroke } = props;
    if (cx == null || cy == null) return <g />;
    return (
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={stroke || "#ff7a33"}
        stroke="#0b0f14"
        strokeWidth={1}
        style={{ cursor: "pointer" }}
        onClick={() => payload?.period && selectPeriod(payload.period, "month")}
      />
    );
  }

  const monthNames = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
  ];

  // ---------- rendu ----------
  if (loading) {
    return (
      <div>
        <h2 className="page-title">Calendrier des feux</h2>
        <div className="panel">
          <LoadingState message="Chargement des séries temporelles…" />
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div>
        <h2 className="page-title">Calendrier des feux</h2>
        <ErrorState error={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  const origin = fc?.data_origin || "—";
  const isSynthetic = origin === "synthetic_fixture";

  return (
    <div>
      <h2 className="page-title">Calendrier des feux</h2>
      <p className="page-sub">
        Évolution temporelle des observations de points chauds (configuration
        primaire d'analyse). Les valeurs mesurent un recouvrement d'ensembles
        entre capteurs, pas une validation au sol.
      </p>

      {isSynthetic ? (
        <div className="banner warn">
          <strong>Origine des données : échantillon synthétique</strong> Les
          séries ci-dessous proviennent de la fixture de démonstration — elles
          valident le pipeline, ce ne sont pas des mesures réelles.
        </div>
      ) : (
        <div className="banner info">
          <strong>Origine des données : {origin}</strong>
          {fc?.generated_at ? ` · artefacts du ${fc.generated_at.slice(0, 10)}` : ""}
        </div>
      )}

      {/* ---------- filtres ---------- */}
      <div className="controls">
        <label>Paire</label>
        <select value={pair} onChange={(e) => setPair(e.target.value)}>
          <option value="all">Toutes les paires</option>
          {pairs.map((p) => (
            <option key={p} value={p}>
              {pairLabel(p)}
            </option>
          ))}
        </select>
        <DateRangeFilter
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          minDate="2013-01-01"
          maxDate="2020-12-31"
        />
        <label> Agrégation </label>
        <span className="seg">
          {GRANULARITIES.map((g) => (
            <button
              key={g.id}
              className={granularity === g.id ? "on" : ""}
              onClick={() => setGranularity(g.id)}
            >
              {g.label}
            </button>
          ))}
        </span>
      </div>

      {/* ---------- indicateurs ---------- */}
      <div className="cards">
        <StatCard
          title="Observations (période)"
          value={stats.sum}
          unit="enregistrements"
          description="a_only + b_only, période filtrée"
        />
        <StatCard
          title="Jours avec enregistrements"
          value={stats.daysWithData}
          unit="jours"
          description="sur la période affichée"
        />
        <StatCard
          title="Pic journalier"
          value={stats.peak}
          unit="observations"
          description="maximum sur une journée"
        />
        <StatCard
          title="Jaccard moyen"
          value={stats.jMean == null ? "—" : stats.jMean.toFixed(3)}
          description="config. primaire, par mois"
        />
      </div>

      {/* ---------- calendrier quotidien ---------- */}
      <div className="panel">
        <h3>
          Calendrier quotidien
          <span className="hint">
            intensité = observations du jour (a_only + b_only)
          </span>
        </h3>
        <div className="cal-head">
          <button className="btn" onClick={() => shiftMonth(-1)}>
            ←
          </button>
          <strong className="mono">
            {monthNames[calCursor.m]} {calCursor.y}
          </strong>
          <button className="btn" onClick={() => shiftMonth(1)}>
            →
          </button>
        </div>
        <div className="cal-grid">
          {WEEKDAYS.map((d, i) => (
            <div key={i} className="cal-dow">
              {d}
            </div>
          ))}
          {calDays.map((cell, i) => {
            if (!cell) return <div key={`b${i}`} className="cal-day out" />;
            const t = cell.stats?.total || 0;
            const pct = cell.stats ? 12 + Math.round((t / maxDayTotal) * 78) : 0;
            return (
              <button
                key={cell.iso}
                className={`cal-day${selected?.kind === "day" && selected.label === cell.iso ? " sel" : ""}`}
                style={
                  cell.stats
                    ? { background: `color-mix(in srgb, var(--ember) ${pct}%, var(--panel-2))` }
                    : undefined
                }
                onClick={() => selectPeriod(cell.iso, "day")}
                title={
                  cell.stats
                    ? `${cell.iso} — ${fmt(t)} observations`
                    : `${cell.iso} — aucun enregistrement`
                }
              >
                <span className="n">{cell.day}</span>
                {cell.stats ? <span className="v">{fmt(t)}</span> : null}
              </button>
            );
          })}
        </div>
        <div className="cal-legend">
          <span>moins</span>
          {[15, 35, 60, 85].map((p) => (
            <span
              key={p}
              className="sw"
              style={{
                background: `color-mix(in srgb, var(--ember) ${p}%, var(--panel-2))`,
              }}
            />
          ))}
          <span>plus</span>
          <span className="muted small" style={{ marginLeft: "auto" }}>
            cliquer un jour pour le détail
          </span>
        </div>
      </div>

      {/* ---------- graphique principal ---------- */}
      <div className="panel">
        <h3>
          Observations par {granularity === "day" ? "jour" : granularity === "week" ? "semaine ISO" : "mois"}
          <span className="hint">total = a_only + b_only</span>
        </h3>
        {series.length === 0 ? (
          <EmptyState message="Aucun enregistrement sur cette période" />
        ) : granularity === "month" ? (
          <div className="chart-box tall">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#23303f" />
                <XAxis dataKey="period" tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#182231", border: "1px solid #23303f" }}
                  formatter={(v) => fmt(v)}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="total"
                  name="Observations"
                  stroke="#ff7a33"
                  strokeWidth={1.8}
                  dot={monthDot}
                />
                <Line
                  type="monotone"
                  dataKey="both"
                  name="Communes"
                  stroke="#35c8c0"
                  strokeWidth={1.8}
                  dot={monthDot}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="chart-box tall">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series} onClick={onBarClick}>
                <CartesianGrid strokeDasharray="3 3" stroke="#23303f" />
                <XAxis dataKey="period" tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#182231", border: "1px solid #23303f" }}
                  formatter={(v) => fmt(v)}
                />
                <Legend />
                <Bar dataKey="total" name="Observations" fill="#ff7a33" onClick={onBarClick} />
                <Bar dataKey="both" name="Communes" fill="#35c8c0" onClick={onBarClick} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
        <p className="legend-note">
          « Observations » = a_only + b_only (détections propres à chaque
          capteur) ; « Communes » = cellules communes aux deux capteurs. Un
          jour/mois vide signifie <em>aucun enregistrement</em>, pas une
          absence de feu avérée.
        </p>
      </div>

      {/* ---------- Jaccard ---------- */}
      <div className="panel">
        <h3>
          Jaccard mensuel
          <span className="hint">configuration primaire — recouvrement, pas précision</span>
        </h3>
        {jaccardByMonth.length === 0 ? (
          <EmptyState message="Aucune série de Jaccard disponible" />
        ) : (
          <div className="chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={jaccardByMonth}>
                <CartesianGrid strokeDasharray="3 3" stroke="#23303f" />
                <XAxis dataKey="period" tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <YAxis
                  domain={[0, 1]}
                  tick={{ fill: "#8ba0b8", fontSize: 11 }}
                  tickFormatter={(v) => v.toFixed(1)}
                />
                <Tooltip
                  contentStyle={{ background: "#182231", border: "1px solid #23303f" }}
                />
                <Legend />
                {pairs.map((p) => (
                  <Line
                    key={p}
                    type="monotone"
                    dataKey={p}
                    name={pairLabel(p)}
                    stroke={PAIR_COLORS[p] || "#5aa7ff"}
                    dot={false}
                    strokeWidth={1.6}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
        <p className="legend-note">
          Le Jaccard mesure le recouvrement d'ensembles entre capteurs sur la
          configuration primaire ; il croît mécaniquement avec la maille et la
          fenêtre — ce n'est pas une précision.
        </p>
      </div>

      {/* ---------- détail période ---------- */}
      {selected && (
        <div className="panel">
          <h3>
            Détail — {selected.label}
            <span className="hint">
              {selected.kind === "day" ? "jour" : selected.kind === "week" ? "semaine ISO" : "mois"}
            </span>
          </h3>
          <div className="table-wrap">
            <table className="data">
              <tbody>
                <tr>
                  <td className="txt"><strong>Période</strong></td>
                  <td className="mono">{selected.label}</td>
                </tr>
                <tr>
                  <td className="txt"><strong>Observations A seulement</strong></td>
                  <td>{fmt(selected.stats.a_only)}</td>
                </tr>
                <tr>
                  <td className="txt"><strong>Observations B seulement</strong></td>
                  <td>{fmt(selected.stats.b_only)}</td>
                </tr>
                <tr>
                  <td className="txt"><strong>Communes</strong></td>
                  <td>{fmt(selected.stats.both)}</td>
                </tr>
                <tr>
                  <td className="txt"><strong>Total</strong></td>
                  <td>{fmt(selected.stats.total)}</td>
                </tr>
                {selected.jaccards?.map((j) => (
                  <tr key={j.pair}>
                    <td className="txt">
                      <strong>Jaccard {pairLabel(j.pair)}</strong>
                    </td>
                    <td>{j.value.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted small" style={{ marginTop: 10 }}>
            « A seulement » / « B seulement » : enregistrements propres à chaque
            capteur de la paire ; « Communes » : cellules partagées. Aucune de
            ces valeurs n'implique une absence de feu.
          </p>
        </div>
      )}
    </div>
  );
}
