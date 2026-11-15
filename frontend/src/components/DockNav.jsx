/**
 * DockNav — barre de navigation centrale du mode carte.
 *
 * Props: { active: "map" | "overview" | "calendar" | "jobs" | "dq" | "risk", onSelect: (view: string) => void }
 */

import { useI18n } from "../i18n/index.jsx";
import Icons from "./icons.jsx";

const NAV_ITEMS = [
  { id: "map", key: "nav.map", icon: "map" },
  { id: "overview", key: "nav.overview", icon: "target" },
  { id: "calendar", key: "nav.calendar", icon: "cal" },
  { id: "jobs", key: "nav.jobs", icon: "cpu" },
  { id: "dq", key: "nav.quality", icon: "checks" },
  { id: "risk", key: "nav.risk", icon: "flame" },
];

export default function DockNav({ active, onSelect }) {
  const { t } = useI18n();

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
            title={t(item.key, item.id)}
            onClick={() => onSelect(item.id)}
          >
            <Icons name={item.icon} className="ic" ariaHidden size={18} />
            <span className="lbl">{t(item.key, item.id)}</span>
          </button>
        );
      })}
    </nav>
  );
}
