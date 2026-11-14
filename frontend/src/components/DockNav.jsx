/**
 * DockNav — barre de navigation centrale du mode carte.
 *
 * Props: { active: "map" | "overview" | "calendar" | "jobs" | "dq" | "risk", onSelect: (view: string) => void }
 */

import Icons from "./icons.jsx";

const NAV_ITEMS = [
  { id: "map", label: "Carte", icon: "map" },
  { id: "overview", label: "Aperçu", icon: "target" },
  { id: "calendar", label: "Calendrier", icon: "cal" },
  { id: "jobs", label: "Jobs", icon: "cpu" },
  { id: "dq", label: "Qualité", icon: "checks" },
  { id: "risk", label: "Risque", icon: "flame" },
];

export default function DockNav({ active, onSelect }) {
  return (
    <nav className="dock" aria-label="Vues de l'application">
      {NAV_ITEMS.map((item) => {
        const isOn = active === item.id;
        return (
          <button
            key={item.id}
            type="button"
            className={`navbtn${isOn ? " on" : ""}`}
            aria-current={isOn ? "true" : undefined}
            title={item.label}
            onClick={() => onSelect(item.id)}
          >
            <Icons name={item.icon} className="ic" ariaHidden size={18} />
            <span className="lbl">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
