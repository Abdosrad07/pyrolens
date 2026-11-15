/**
 * RiskView — vue pleine page Risque.
 *
 * Affiche la carte avec la couche risque activée + le panneau de configuration.
 */

import { useState } from "react";
import { useI18n } from "../i18n/index.jsx";
import RiskPanel from "../components/RiskPanel.jsx";

export default function RiskView({ riskData, riskThreshold, setRiskThreshold, showRisk, setShowRisk }) {
  const { t } = useI18n();
  const [panelOpen, setPanelOpen] = useState(false);

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", background: "var(--ash)" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "1.2rem 2rem", background: "#fff", borderBottom: "1px solid var(--mist)" }}>
          <h2 style={{ font: "700 1.3rem var(--display)", margin: 0 }}>{t("risk.title", "Couche risque de feu")}</h2>
          <small style={{ color: "var(--muted)" }}>
            {t("risk.subtitle", "Prédiction probabiliste · {g}° grid · Cameroon coverage").replace("{g}", "0.25")}
          </small>
        </div>
        <div style={{ flex: 1, position: "relative" }}>
          {/* Carte RiskView = carte avec risque toujours activé, voir MapView intégré dans App */}
          <div style={{
            position: "absolute", inset: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--muted)", fontSize: "0.9rem"
          }}>
            {t("risk.hint", "Activez la vue Carte pour afficher la couche risque sur la carte interactive.")}
            <br />
            {t("risk.hint2", "Ouvrez le panneau de configuration avec la sphère flottante.")}
          </div>
        </div>
      </div>
      <RiskPanel open={panelOpen} onClose={() => setPanelOpen(false)} />
    </div>
  );
}
