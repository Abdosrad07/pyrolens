/**
 * HamburgerMenu — panneau latéral avec les modes de visualisation.
 *
 * Props: { open: boolean, onClose: () => void, onSelect: (view: string) => void }
 *
 * Liste les 6 vues de l'application avec leur icône et description.
 */

import { useI18n } from "../i18n/index.jsx";
import Icons from "./icons.jsx";

const MODES = [
  { id: "map", icon: "map", desc: "Carte interactive avec tuiles GIBS et couche de risque" },
  { id: "overview", icon: "target", desc: "Tableau de bord d'exploration — synthèse du pipeline" },
  { id: "calendar", icon: "cal", desc: "Calendrier des feux — divergence inter-capteurs par jour" },
  { id: "harmonization", icon: "sliders", desc: "Harmonisation Lab — graphes de recouvrement VIIRS/MODIS" },
  { id: "jobs", icon: "cpu", desc: "Tâches asynchrones — harmonisation, analyse FIRMS, entraînement" },
  { id: "dq", icon: "checks", desc: "Qualité des données — rapport de contrôle et anomalies" },
  { id: "risk", icon: "flame", desc: "Risque de feu — modèle RF calibré, probabilités par cellule" },
];

export default function HamburgerMenu({ open, onClose, onSelect, active }) {
  const { t } = useI18n();
  if (!open) return null;

  return (
    <div
      className="hamburger-overlay"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        zIndex: 2000,
        display: "flex",
        justifyContent: "flex-end",
      }}
    >
      <div
        className="hamburger-panel"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "20rem",
          maxWidth: "90vw",
          background: "var(--panel, #0e2e29)",
          color: "#fff",
          padding: "1.2rem",
          overflowY: "auto",
          borderLeft: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, opacity: 0.8 }}>
            {t("hamburger.title", "Modes de visualisation")}
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("hamburger.close", "Fermer")}
            style={{
              background: "none",
              border: "none",
              color: "rgba(255,255,255,0.6)",
              cursor: "pointer",
              fontSize: "1.4rem",
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => { onSelect(m.id); onClose(); }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.8rem",
                width: "100%",
                padding: "0.8rem 1rem",
                background: active === m.id ? "rgba(255,255,255,0.08)" : "transparent",
                border: "none",
                borderRadius: "0.5rem",
                color: "#fff",
                cursor: "pointer",
                textAlign: "left",
                transition: "background 0.15s",
              }}
            >
              <Icons name={m.icon} ariaHidden size={20} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                  {t(`nav.${m.id}`, m.id)}
                </div>
                <div style={{ fontSize: "0.72rem", opacity: 0.6, marginTop: "0.1rem" }}>
                  {m.desc}
                </div>
              </div>
            </button>
          ))}
        </nav>

        <div style={{ marginTop: "1.2rem", paddingTop: "1rem", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
          <small style={{ opacity: 0.4, fontSize: "0.7rem" }}>
            PyroLens — NASA Space Apps 2026
          </small>
        </div>
      </div>
    </div>
  );
}
