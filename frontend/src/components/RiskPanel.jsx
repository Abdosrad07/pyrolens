/**
 * RiskPanel — panneau latéral coulissant (gauche) pour la configuration et les résultats
 * du modèle de prédiction de risque.
 *
 * Props: { open: boolean, onClose: () => void }
 * State interne :
 *  - showLayer: checkbox "afficher la couche risque"
 *  - grid: 0.10 / 0.25 / 0.50
 *  - window: 1 / 4 / 8 / 16 jours
 *  - date: date de référence (ISO)
 *  - threshold: seuil 0–100%
 *  - running: état chargement pour "Exécuter prédiction"
 */

import { useState, useEffect } from "react";
import { useI18n } from "../i18n/index.jsx";
import Icons from "./icons.jsx";
import useRiskData from "../hooks/useRiskData.js";
import useApi from "../hooks/useApi.js";

const GRID_OPTS = ["0.10", "0.25", "0.50"];
const WIN_OPTS = ["1", "4", "8", "16"];

export default function RiskPanel({ open, onClose }) {
  const { t } = useI18n();
  const [showLayer, setShowLayer] = useState(true);
  const [grid, setGrid] = useState("0.25");
  const [window, setWindow] = useState("8");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [threshold, setThreshold] = useState(0);
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState("");
  const [showLog, setShowLog] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);

  const { riskData, loading, reload, metrics, cellsCount, highCells, origin, generatedAt } =
    useRiskData();
  const api = useApi();

  useEffect(() => {
    if (open && !riskData && !loading) reload();
  }, [open]);

  const statusCls =
    riskData && !loading
      ? "rp-status ok"
      : loading
        ? "rp-status warn"
        : "rp-status err";
  const statusText =
    riskData && !loading
      ? t("riskPanel.status.ok")
      : loading
        ? t("riskPanel.status.loading")
        : t("riskPanel.status.error");

  const handleRun = async () => {
    setRunning(true);
    setShowLog(true);
    setLog(
      `Launch: grid ${grid}°, window ${window} d, reference ${date || "max data"}\n` +
      "(backend job — may take ~10 min on real data)\n"
    );
    try {
      const job = await api.predict({
        grid_deg: +grid,
        window: +window,
        reference_date: date || null,
      });
      setLog((prev) => prev + `\nJob ${job.job_id} — ${job.status}\n`);
      const poll = async () => {
        try {
          const j = await api.getPredictJob(job.job_id);
          const p = j.progress || {};
          setLog(
            (prev) =>
              prev
                .split("\n")
                .filter((l) => !l.startsWith("→"))
                .join("\n") +
              `\n→ ${p.step || j.status} ${Math.round(p.pct || 0)}% ${p.detail || ""}`.trimEnd()
          );
          if (j.status === "succeeded") {
            setLog((prev) => prev + "\n✓ Training complete — reloading artifact…");
            await reload();
            setRunning(false);
            return;
          }
          if (j.status === "failed") {
            setLog((prev) => prev + `\n✗ Failed: ${j.error || "unknown error"}`);
            setRunning(false);
            return;
          }
          setTimeout(poll, 5000);
        } catch (e) {
          setLog((prev) => prev + `\n✗ Polling: ${e.message}`);
          setRunning(false);
        }
      };
      poll();
    } catch (e) {
      setLog((prev) => prev + `\n✗ Launch refused: ${e.message}`);
      setRunning(false);
    }
  };

  const handleLoad = async () => {
    setShowLog(true);
    setLog("Loading fire_risk.json…");
    await reload();
    if (riskData) {
      setLog(
        `✓ Loaded: ${riskData.cells?.length || 0} cells\n` +
        `Source: ${riskData.data_origin || "?"}\n` +
        `Generated: ${riskData.generated_at || "?"}`
      );
    }
  };

  const prAuc = metrics.pr_auc;
  const f1 = metrics.f1;
  const brier = metrics.brier;
  const baseline = metrics.baseline_pr_auc;

  return (
    <aside
      id="riskPanel"
      className={`risk-panel${open ? " open" : ""}`}
      aria-label="Analyse de risque de feu"
      aria-hidden={!open}
    >
      <div className="rp-head">
        <Icons name="flame" className="ic" ariaHidden size={18} />
        <h2>{t("riskPanel.title", "Analyse de risque de feu")}</h2>
        <span className={statusCls}>{statusText}</span>
        <button className="ibtn" type="button" title="Fermer" aria-label="Fermer le panneau risque" onClick={onClose}>
          <Icons name="x" className="ic" ariaHidden size={18} />
        </button>
      </div>

      <div className="rp-scroll">
        {/* Configuration */}
        <div className="rp-section">
          <h3>{t("riskPanel.config", "Configuration")}</h3>
          <div className="rp-toggle">
            <input
              type="checkbox"
              id="rpToggle"
              role="switch"
              checked={showLayer}
              onChange={(e) => setShowLayer(e.target.checked)}
            />
            <label htmlFor="rpToggle">{t("riskPanel.toggleLayer", "Afficher la couche risque")}</label>
          </div>
          <div className="rp-row">
            <label htmlFor="rpGrid">{t("riskPanel.grid", "Grille (°)")}</label>
            <select id="rpGrid" value={grid} onChange={(e) => setGrid(e.target.value)}>
              {GRID_OPTS.map((g) => (
                <option key={g} value={g}>{g}°</option>
              ))}
            </select>
          </div>
          <div className="rp-row">
            <label htmlFor="rpWindow">{t("riskPanel.window", "Fenêtre (jours)")}</label>
            <select id="rpWindow" value={window} onChange={(e) => setWindow(e.target.value)}>
              {WIN_OPTS.map((w) => (
                <option key={w} value={w}>{w} {t("riskPanel.windowDays", "jours")}</option>
              ))}
            </select>
          </div>
          <div className="rp-row">
            <label htmlFor="rpDate">{t("riskPanel.date", "Date de référence")}</label>
            <input
              id="rpDate"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          <div className="rp-row">
            <label htmlFor="rpThreshold">{t("riskPanel.threshold", "Seuil d'affichage")}</label>
            <input
              id="rpThreshold"
              type="range"
              min={0}
              max={100}
              value={threshold}
              step={1}
              onChange={(e) => setThreshold(+e.target.value)}
            />
            <span className="thr-val">{threshold}%</span>
          </div>
          <div className="rp-actions">
            <button className="rp-btn" type="button" onClick={handleRun}>
              <Icons name="cpu" className="ic" ariaHidden size={16} />
              {t("riskPanel.run", "Exécuter prédiction")}
            </button>
            <button className="rp-btn rp-btn-secondary" type="button" onClick={handleLoad}>
              <Icons name="download" className="ic" ariaHidden size={16} />
              {t("riskPanel.load", "Charger artefact")}
            </button>
          </div>
        </div>

        {/* Bandeau honnêteté */}
        <div className="rp-section">
          <h3>{t("riskPanel.honesty", "Bandeau honnêteté")}</h3>
          <div className="honesty">
            <b>{t("riskPanel.honestyText", "Estimation du risque d'activité de feu détectée").replace("<b>", "").replace("</b>", "")} </b>— {t("riskPanel.honestyTail", "pas une alerte incendie")}
            <small>
              {riskData
                ? `${t("riskPanel.honestyData", "données {origin} · généré le {generatedAt}", { origin, generatedAt })}` +
                  (prAuc != null ? ` · PR-AUC ${prAuc.toFixed(3)}` : "") +
                  (f1 != null ? ` · F1 ${f1.toFixed(3)}` : "") +
                  (brier != null ? ` · Brier ${brier.toFixed(3)}` : "") +
                  (baseline != null ? ` · baseline ${baseline.toFixed(3)}` : "")
                : t("riskPanel.waiting", "Module de prédiction en attente de données")}
            </small>
          </div>
        </div>

        {/* Métriques */}
        {riskData && (prAuc != null || f1 != null) && (
          <div className="rp-section">
            <h3>{t("riskPanel.metrics", "Métriques du modèle")}</h3>
            <div className="metrics-grid">
              {prAuc != null && (
                <div className="metric-card">
                  <div className="mk">{t("riskPanel.metricPR", "PR-AUC")}</div>
                  <div className="mv">{prAuc.toFixed(3)}</div>
                </div>
              )}
              {f1 != null && (
                <div className="metric-card">
                  <div className="mk">{t("riskPanel.metricF1", "F1")}</div>
                  <div className="mv">{f1.toFixed(3)}</div>
                </div>
              )}
              {brier != null && (
                <div className="metric-card">
                  <div className="mk">{t("riskPanel.metricBrier", "Brier")}</div>
                  <div className="mv">{brier.toFixed(3)}</div>
                </div>
              )}
              {baseline != null && (
                <div className="metric-card">
                  <div className="mk">{t("riskPanel.metricBaseline", "Baseline")}</div>
                  <div className="mv">{baseline.toFixed(3)}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Journal d'exécution */}
        {showLog && (
          <div className="rp-section">
            <h3>{t("riskPanel.log", "Journal d'exécution")}</h3>
            <pre className="risk-log">{log}</pre>
          </div>
        )}
      </div>
    </aside>
  );
}
