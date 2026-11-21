/**
 * EarlyWarningView — Early Warning Center.
 *
 * Dashboard de surveillance des anomalies statistiques d'activité de feu
 * détectée par satellite. Comparaison récent vs baseline historique.
 *
 * États gérés : loading / data / error / empty / mock.
 * Layout : KPI en haut, liste d'alertes + carte à gauche, détails à droite.
 */

import { useState, useMemo, useCallback } from "react";
import { useI18n } from "../i18n/index.jsx";
import useEarlyWarning from "../hooks/useEarlyWarning.js";
import EarlyWarningMap from "../components/EarlyWarningMap.jsx";
import EarlyWarningChart from "../components/EarlyWarningChart.jsx";

const SEV_COLOR = {
  critical: "var(--bad)",
  high: "var(--ember)",
  moderate: "var(--warn)",
  low: "var(--ok)",
};

/** Cartouche KPI. */
function KpiCard({ label, value, sub, accent }) {
  return (
    <div className="card">
      <div className="k">{label}</div>
      <div className="v" style={accent ? { color: accent } : undefined}>{value}</div>
      {sub && <div className="u">{sub}</div>}
    </div>
  );
}

/** Badge de sévérité. */
function SevBadge({ severity }) {
  const c = SEV_COLOR[severity] || "var(--muted)";
  return (
    <span style={{
      display: "inline-block",
      padding: "0.15rem 0.5rem",
      borderRadius: "999px",
      fontSize: "0.7rem",
      fontWeight: 700,
      letterSpacing: "0.02em",
      color: "#fff",
      background: c,
      textTransform: "uppercase",
    }}>
      {severity}
    </span>
  );
}

export default function EarlyWarningView({ onBack }) {
  const { t } = useI18n();
  const { loading, error, summary, alerts, selected, select, usingMock, reload } = useEarlyWarning();
  const [sortKey, setSortKey] = useState("severity"); // "severity" | "activity"
  const [sevFilter, setSevFilter] = useState("all");

  const filtered = useMemo(() => {
    let list = alerts;
    if (sevFilter !== "all") list = list.filter((a) => a.severity === sevFilter);
    if (sortKey === "activity") {
      list = [...list].sort((x, y) => (y.recent_detections || 0) - (x.recent_detections || 0));
    } else {
      const rank = { critical: 0, high: 1, moderate: 2, low: 3 };
      list = [...list].sort((x, y) => rank[x.severity] - rank[y.severity] || (y.recent_detections || 0) - (x.recent_detections || 0));
    }
    return list;
  }, [alerts, sortKey, sevFilter]);

  // Sync carte <-> liste : clic sur une alerte de la liste sélectionne aussi sur la carte
  const handleSelect = useCallback((a) => select(a), [select]);

  const period = summary?.data_period;
  const generated = summary?.generated_at
    ? new Date(summary.generated_at).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" })
    : null;

  // ── États limites ──
  if (loading) {
    return (
      <div className="content">
        <ViewHeader onBack={onBack} title={t("ew.title", "Early Warning Center")} />
        <p className="empty" style={{ opacity: 0.5 }}>{t("ew.loading", "Chargement des données d'anomalies…")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="content">
        <ViewHeader onBack={onBack} title={t("ew.title", "Early Warning Center")} />
        <div className="banner warn">
          <b>{t("ew.apiError", "API indisponible :")}</b> {error}
          <div style={{ marginTop: "0.6rem" }}>
            <button className="btn-back" type="button" onClick={reload}>
              {t("ew.retry", "Réessayer")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isEmpty = alerts.length === 0;

  return (
    <div className="content">
      <ViewHeader onBack={onBack} title={t("ew.title", "Early Warning Center")} />

      {/* Avertissement données historiques / mock */}
      {(summary?.historical_backtest || usingMock) && (
        <div className="banner warn" style={{ marginTop: "0.4rem" }}>
          <b>{t("ew.backtest", "Résultats analytiques historiques — pas d'alertes en direct.")}</b>{" "}
          {t("ew.backtestNote", "Ces signaux proviennent d'un backtest sur données passées. Ils n'impliquent aucune prédiction en temps réel d'incendie.")}
        </div>
      )}

      {/* Période + origine */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem 1.2rem", marginTop: "0.6rem", fontSize: "0.8rem", color: "var(--muted)" }}>
        {period && (
          <span>
            {t("ew.period", "Période")} : {period.start} → {period.end} ({period.days} j)
          </span>
        )}
        <span>{t("ew.origin", "Origine")}: {summary?.data_origin || "—"}</span>
        {generated && <span>{t("ew.generated", "Généré")}: {generated}</span>}
      </div>

      {/* KPI */}
      <div className="cards">
        <KpiCard label={t("ew.kpi.cells", "Cellules surveillées")} value={summary?.n_cells_monitored ?? "—"} />
        <KpiCard label={t("ew.kpi.anomalies", "Anomalies détectées")} value={summary?.n_anomalies ?? "—"} accent="var(--ember)" />
        <KpiCard label={t("ew.kpi.high", "Alertes priorité élevée")} value={summary?.n_high_priority ?? "—"} accent="var(--bad)" />
        <KpiCard label={t("ew.kpi.zones", "Zones en hausse d'activité")} value={summary?.n_increasing_zones ?? "—"} accent="var(--lagoon)" />
      </div>

      {/* Contrôles : tri + filtre */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center", margin: "1.2rem 0 0.6rem" }}>
        <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
          {t("ew.sort", "Trier par")}
          <select value={sortKey} onChange={(e) => setSortKey(e.target.value)} style={selStyle}>
            <option value="severity">{t("ew.sort.sev", "Sévérité")}</option>
            <option value="activity">{t("ew.sort.act", "Activité")}</option>
          </select>
        </label>
        <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
          {t("ew.filter", "Filtrer")}
          <select value={sevFilter} onChange={(e) => setSevFilter(e.target.value)} style={selStyle}>
            <option value="all">{t("ew.filter.all", "Tous niveaux")}</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="moderate">Moderate</option>
            <option value="low">Low</option>
          </select>
        </label>
        <span style={{ marginLeft: "auto", fontSize: "0.78rem", color: "var(--muted)" }}>
          {filtered.length} / {alerts.length} {t("ew.alerts", "alertes")}
        </span>
      </div>

      {/* Liste vide */}
      {isEmpty ? (
        <div className="banner info">
          {t("ew.none.title", "Aucune anomalie détectée sur la période.")}{" "}
          {t("ew.none.note", "Toutes les cellules restent dans l'enveloppe de leur baseline historique.")}
        </div>
      ) : (
        /* Layout 2 colonnes : liste + carte | détails (→ 1 colonne sur mobile) */
        <div className="ew-grid">
          <div>
            {/* Liste d'alertes */}
            <h3 style={{ fontSize: "0.95rem", margin: "0 0 0.5rem" }}>{t("ew.listTitle", "Alertes classées")}</h3>
            <table className="jl" style={{ marginBottom: "1.2rem" }}>
              <thead>
                <tr>
                  <th>{t("ew.th.sev", "Niveau")}</th>
                  <th>{t("ew.th.cell", "Cellule")}</th>
                  <th>{t("ew.th.recent", "Récent")}</th>
                  <th>{t("ew.th.base", "Baseline")}</th>
                  <th>{t("ew.th.change", "Variation")}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((a) => {
                  const isSel = selected?.cell_id === a.cell_id;
                  return (
                    <tr
                      key={a.cell_id}
                      tabIndex={0}
                      onClick={() => handleSelect(a)}
                      onKeyDown={(e) => e.key === "Enter" && handleSelect(a)}
                      style={{ cursor: "pointer", background: isSel ? "var(--ok-bg)" : undefined, outline: isSel ? "2px solid var(--lagoon)" : undefined }}
                    >
                      <td><SevBadge severity={a.severity} /></td>
                      <td><code>{a.cell_id}</code></td>
                      <td>{a.recent_detections}</td>
                      <td>{a.historical_baseline}</td>
                      <td style={{ color: a.activity_change > 0 ? "var(--ember)" : "var(--ok)", fontWeight: 700 }}>
                        {a.activity_change > 0 ? "+" : ""}{a.activity_change}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Carte */}
            <h3 style={{ fontSize: "0.95rem", margin: "0 0 0.5rem" }}>{t("ew.mapTitle", "Distribution géographique")}</h3>
            <div style={{ height: "340px", borderRadius: "var(--r-m)", overflow: "hidden" }}>
              <EarlyWarningMap alerts={filtered} selected={selected} onSelect={handleSelect} />
            </div>
          </div>

          {/* Détails de l'alerte sélectionnée */}
          <div>
            <h3 style={{ fontSize: "0.95rem", margin: "0 0 0.5rem" }}>{t("ew.detailsTitle", "Détails de l'alerte")}</h3>
            {selected ? (
              <AlertDetails alert={selected} />
            ) : (
              <div className="banner info">
                {t("ew.selectHint", "Sélectionnez une alerte dans la liste ou sur la carte pour afficher son détail.")}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const selStyle = {
  minHeight: "2.4rem",
  padding: "0 0.6rem",
  fontSize: "0.8rem",
  background: "#fff",
  border: "1.5px solid var(--mist)",
  borderRadius: "var(--r-s)",
};

/** En-tête de vue avec retour. */
function ViewHeader({ onBack, title }) {
  return (
    <>
      {onBack && (
        <button className="btn-back" type="button" onClick={onBack} style={{ marginBottom: "0.8rem" }}>
          ← {onBack ? "Retour à la carte" : ""}
        </button>
      )}
      <h2>{title}</h2>
    </>
  );
}

/** Panneau de détails d'une alerte sélectionnée. */
function AlertDetails({ alert }) {
  const { t } = useI18n();
  const rows = [
    [t("ew.d.coords", "Coordonnées"), `${alert.lat?.toFixed(2)}°, ${alert.lon?.toFixed(2)}°`],
    [t("ew.d.sev", "Niveau"), alert.severity],
    [t("ew.d.recent", "Détections récentes"), String(alert.recent_detections)],
    [t("ew.d.base", "Médiane historique"), String(alert.historical_baseline)],
    [t("ew.d.score", "Score d'anomalie"), String(alert.anomaly_score ?? "—")],
    [t("ew.d.persist", "Persistance"), `${alert.persistence} ${t("ew.d.persistUnit", "jours")}`],
    [t("ew.d.sensors", "Capteurs"), (alert.sensors || []).join(", ")],
    [t("ew.d.period", "Période d'observation"), `${alert.observation_period?.start} → ${alert.observation_period?.end}`],
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.6rem" }}>
          <SevBadge severity={alert.severity} />
          <strong style={{ fontSize: "1rem" }}>Cellule {alert.cell_id}</strong>
        </div>
        <table className="dt">
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k}><td style={{ width: "11rem" }}>{k}</td><td>{v}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Graphique récent vs historique */}
      <div style={{ background: "#fff", border: "1px solid var(--mist)", borderRadius: "var(--r-m)", padding: "0.8rem" }}>
        <EarlyWarningChart alert={alert} />
      </div>

      {/* Raison de l'alerte */}
      <div>
        <h4 style={{ margin: "0 0 0.3rem", fontSize: "0.85rem" }}>{t("ew.d.reason", "Raison de l'alerte")}</h4>
        <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text)", lineHeight: 1.5 }}>{alert.reason}</p>
      </div>

      {/* Limites */}
      {alert.limitations?.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 0.3rem", fontSize: "0.85rem" }}>{t("ew.d.limits", "Limites de l'interprétation")}</h4>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.82rem", color: "var(--muted)" }}>
            {alert.limitations.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
