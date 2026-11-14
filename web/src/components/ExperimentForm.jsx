/**
 * ExperimentForm - 5-step wizard for creating experiments
 * Used by: HarmonizationNew
 * 
 * @param {function} onSubmit - Callback when form is submitted
 * @param {function} onCancel - Callback when form is cancelled
 */
import { useState } from "react";
import { PAIR_LABELS } from "../data.js";
import DatasetSelector from "./DatasetSelector.jsx";
import SpatialParamSelector from "./SpatialParamSelector.jsx";
import TemporalParamSelector from "./TemporalParamSelector.jsx";

const PAIRS = [
  { id: "terra__aqua", label: "Terra – Aqua" },
  { id: "aqua__viirs_snpp", label: "Aqua – VIIRS S-NPP" },
];

const STEPS = [
  { id: "pair", label: "1. Paire de capteurs" },
  { id: "dataset", label: "2. Jeu de données" },
  { id: "spatial", label: "3. Paramètres spatiaux" },
  { id: "temporal", label: "4. Paramètres temporels" },
  { id: "review", label: "5. Résumé" },
];

export default function ExperimentForm({ onSubmit, onCancel }) {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    pair: "",
    dataset: "",
    grid_deg: 0.25,
    window_days: 8,
    source: "auto",
  });

  const currentStep = STEPS[step];

  const nextStep = () => {
    if (step < STEPS.length - 1) setStep(step + 1);
  };

  const prevStep = () => {
    if (step > 0) setStep(step - 1);
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const canProceed = () => {
    switch (currentStep.id) {
      case "pair":
        return !!formData.pair;
      case "dataset":
        return !!formData.dataset;
      case "spatial":
        return !!formData.grid_deg;
      case "temporal":
        return !!formData.window_days;
      case "review":
        return true;
      default:
        return false;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "20px" }}>
        {STEPS.map((s, i) => (
          <span
            key={s.id}
            style={{
              display: "inline-block",
              padding: "6px 12px",
              margin: "0 4px 4px 0",
              borderRadius: "4px",
              fontSize: "13px",
              background: i === step ? "var(--panel-2)" : "transparent",
              color: i === step ? "var(--text)" : "var(--muted)",
              border: i === step ? "1px solid var(--line)" : "1px solid transparent",
            }}
          >
            {s.label}
          </span>
        ))}
      </div>

      <div className="panel">
        {currentStep.id === "pair" && (
          <div>
            <h3>Choisissez la paire de capteurs à comparer</h3>
            <p className="muted" style={{ marginBottom: "16px" }}>
              Sélectionnez la paire de satellites pour l'analyse d'harmonisation.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {PAIRS.map((p) => (
                <label
                  key={p.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "12px",
                    border: formData.pair === p.id ? "1px solid var(--ember)" : "1px solid var(--line)",
                    borderRadius: "8px",
                    cursor: "pointer",
                    background: formData.pair === p.id ? "rgba(255, 122, 51, 0.1)" : "transparent",
                  }}
                >
                  <input
                    type="radio"
                    name="pair"
                    value={p.id}
                    checked={formData.pair === p.id}
                    onChange={(e) => setFormData({ ...formData, pair: e.target.value })}
                  />
                  <strong>{p.label}</strong>
                </label>
              ))}
            </div>
          </div>
        )}

        {currentStep.id === "dataset" && (
          <div>
            <h3>Sélectionnez le jeu de données source</h3>
            <p className="muted" style={{ marginBottom: "16px" }}>
              Choisissez les données FIRMS à utiliser pour cette expérience.
            </p>
            <DatasetSelector
              datasets={[
                { id: "firms_modis", label: "FIRMS MODIS (Terra + Aqua)" },
                { id: "firms_viirs", label: "FIRMS VIIRS S-NPP" },
              ]}
              selected={formData.dataset}
              onChange={(value) => setFormData({ ...formData, dataset: value })}
            />
          </div>
        )}

        {currentStep.id === "spatial" && (
          <div>
            <h3>Configurez les paramètres spatiaux</h3>
            <p className="muted" style={{ marginBottom: "16px" }}>
              Définissez la résolution de la grille pour l'agrégation spatiale.
            </p>
            <SpatialParamSelector
              gridDeg={formData.grid_deg}
              onChange={(value) => setFormData({ ...formData, grid_deg: value })}
            />
          </div>
        )}

        {currentStep.id === "temporal" && (
          <div>
            <h3>Configurez les paramètres temporels</h3>
            <p className="muted" style={{ marginBottom: "16px" }}>
              Définissez la fenêtre temporelle pour l'agrégation des détections.
            </p>
            <TemporalParamSelector
              windowDays={formData.window_days}
              onChange={(value) => setFormData({ ...formData, window_days: value })}
            />
          </div>
        )}

        {currentStep.id === "review" && (
          <div>
            <h3>Résumé de l'expérience</h3>
            <p className="muted" style={{ marginBottom: "16px" }}>
              Vérifiez les paramètres avant de lancer l'expérience.
            </p>
            <div className="table-wrap">
              <table className="data">
                <tbody>
                  <tr>
                    <td className="txt"><strong>Paire</strong></td>
                    <td>{PAIR_LABELS[formData.pair] || formData.pair}</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Jeu de données</strong></td>
                    <td>{formData.dataset}</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Résolution de grille</strong></td>
                    <td>{formData.grid_deg}°</td>
                  </tr>
                  <tr>
                    <td className="txt"><strong>Fenêtre temporelle</strong></td>
                    <td>{formData.window_days} jours</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: "24px",
            paddingTop: "16px",
            borderTop: "1px solid var(--line)",
          }}
        >
          <button
            className="btn"
            onClick={prevStep}
            disabled={step === 0}
            style={{ opacity: step === 0 ? 0.5 : 1 }}
          >
            ← Précédent
          </button>
          <div style={{ display: "flex", gap: "12px" }}>
            <button className="btn" onClick={onCancel}>
              Annuler
            </button>
            {step === STEPS.length - 1 ? (
              <button className="btn" onClick={handleSubmit} disabled={!canProceed()}>
                Lancer l'expérience
              </button>
            ) : (
              <button className="btn" onClick={nextStep} disabled={!canProceed()}>
                Suivant →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
