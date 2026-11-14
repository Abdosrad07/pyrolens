/**
 * RiskView — vue pleine page Risque.
 *
 * Affiche la carte avec la couche risque activée + le panneau de configuration.
 */

import { useState } from "react";
import RiskPanel from "../components/RiskPanel.jsx";

export default function RiskView({ riskData, riskThreshold, setRiskThreshold, showRisk, setShowRisk }) {
  const [panelOpen, setPanelOpen] = useState(false);

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", background: "var(--ash)" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "1.2rem 2rem", background: "#fff", borderBottom: "1px solid var(--mist)" }}>
          <h2 style={{ font: "700 1.3rem var(--display)", margin: 0 }}>Couche risque de feu</h2>
          <small style={{ color: "var(--muted)" }}>
            Prédiction probabiliste · grille {0.25}° · emprise Cameroun
          </small>
        </div>
        <div style={{ flex: 1, position: "relative" }}>
          {/* Carte RiskView = carte avec risque toujours activé, voir MapView intégré dans App */}
          <div style={{
            position: "absolute", inset: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--muted)", fontSize: "0.9rem"
          }}>
            Activez la vue Carte pour afficher la couche risque sur la carte interactive.
            <br />
            Ouvrez le panneau de configuration avec la sphère flottante.
          </div>
        </div>
      </div>
      <RiskPanel open={panelOpen} onClose={() => setPanelOpen(false)} />
    </div>
  );
}
