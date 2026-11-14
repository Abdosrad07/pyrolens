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
import Icons from "./icons.jsx";
import useRiskData from "../hooks/useRiskData.js";

const GRID_OPTS = ["0.10", "0.25", "0.50"];
const WIN_OPTS = ["1", "4", "8", "16"];

export default function RiskPanel({ open, onClose }) {
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
      ? "Données charagées"
      : loading
        ? "Chargement…"
        : "Indisponible";

  const handleRun = () => {
    setRunning(true);
    setShowLog(true);
    setLog(
      "Le module src/pyrolens/prediction.py sera connecté ici.\n" +
      "En attente de l'implémentation backend.\n\n" +
      "Commande attendue :\n" +
      `  PYTHONPATH=src python3 -m pyrolens.cli predict\n    --grid ${grid} --window ${window}`
    );
  };

  const handleLoad = async () => {
    setShowLog(true);
    setLog("Chargement de fire_risk.json…");
    await reload();
    if (riskData) {
      setLog(
        `✓ Chargé : ${riskData.cells?.length || 0} cellules\n` +
        `Source: ${riskData.data_origin || "?"}\n` +
        `Généré: ${riskData.generated_at || "?"}`
      );
    }
  };

  const prAuc = metrics.pr_auc;
  const f1 = metrics.f1;
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
        <h2>Analyse de risque de feu</h2>
        <span className={statusCls}>{statusText}</span>
        <button className="ibtn" type="button" title="Fermer" aria-label="Fermer le panneau risque" onClick={onClose}>
          <Icons name="x" className="ic" ariaHidden size={18} />
        </button>
      </div>

      <div className="rp-scroll">
        {/* Configuration */}
        <div className="rp-section">
          <h3>Configuration</h3>
          <div className="rp-toggle">
            <input
              type="checkbox"
              id="rpToggle"
              role="switch"
              checked={showLayer}
              onChange={(e) => setShowLayer(e.target.checked)}
            />
            <label htmlFor="rpToggle">Afficher la couche risque</label>
          </div>
          <div className="rp-row">
            <label htmlFor="rpGrid">Grille (°)</label>
            <select id="rpGrid" value={grid} onChange={(e) => setGrid(e.target.value)}>
              {GRID_OPTS.map((g) => (
                <option key={g} value={g}>{g}°</option>
              ))}
            </select>
          </div>
          <div className="rp-row">
            <label htmlFor="rpWindow">Fenêtre (jours)</label>
            <select id="rpWindow" value={window} onChange={(e) => setWindow(e.target.value)}>
              {WIN_OPTS.map((w) => (
                <option key={w} value={w}>{w} jour{w !== "1" ? "s" : ""}</option>
              ))}
            </select>
          </div>
          <div className="rp-row">
            <label htmlFor="rpDate">Date de référence</label>
            <input
              id="rpDate"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          <div className="rp-row">
            <label htmlFor="rpThreshold">Seuil d&apos;affichage</label>
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
              Exécuter prédiction
            </button>
            <button className="rp-btn rp-btn-secondary" type="button" onClick={handleLoad}>
              <Icons name="download" className="ic" ariaHidden size={16} />
              Charger artefact
            </button>
          </div>
        </div>

        {/* Bandeau honnêteté */}
        <div className="rp-section">
          <h3>Bandeau honnêteté</h3>
          <div className="honesty">
            <b>Estimation du risque d&apos;activité de feu détectée</b> — pas une alerte incendie
            <small>
              {riskData
                ? `données ${origin} · généré le ${generatedAt}` +
                  (prAuc != null ? ` · PR-AUC ${prAuc.toFixed(3)}` : "") +
                  (f1 != null ? ` · F1 ${f1.toFixed(3)}` : "") +
                  (baseline != null ? ` · baseline ${baseline.toFixed(3)}` : "")
                : "Module de prédiction en attente de données"}
            </small>
          </div>
        </div>

        {/* Métriques */}
        {riskData && (prAuc != null || f1 != null) && (
          <div className="rp-section">
            <h3>Métriques du modèle</h3>
            <div className="metrics-grid">
              {prAuc != null && (
                <div className="metric-card">
                  <div className="mk">PR-AUC</div>
                  <div className="mv">{prAuc.toFixed(3)}</div>
                </div>
              )}
              {f1 != null && (
                <div className="metric-card">
                  <div className="mk">F1</div>
                  <div className="mv">{f1.toFixed(3)}</div>
                </div>
              )}
              {baseline != null && (
                <div className="metric-card">
                  <div className="mk">Baseline</div>
                  <div className="mv">{baseline.toFixed(3)}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Journal d'exécution */}
        {showLog && (
          <div className="rp-section">
            <h3>Journal d&apos;exécution</h3>
            <pre className="risk-log">{log}</pre>
          </div>
        )}
      </div>
    </aside>
  );
}
