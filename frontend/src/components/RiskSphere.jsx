/**
 * RiskSphere — bouton flottant qui ouvre le panneau IA / Risque.
 *
 * Props: { open: boolean, onClick: () => void, hasData: boolean }
 */

import Icons from "./icons.jsx";

export default function RiskSphere({ open, onClick, hasData = false }) {
  const handleClick = () => onClick?.();
  const handleKey = (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleClick(); }
  };

  return (
    <div
      id="riskSphere"
      role="button"
      tabIndex={0}
      title="Assistant IA"
      aria-label="Ouvrir l’assistant IA"
      aria-expanded={open}
      aria-controls="aiPanel"
      className={`risk-sphere${hasData ? " has-data" : ""}`}
      onClick={handleClick}
      onKeyDown={handleKey}
    >
      <Icons name="flame" className="ic" ariaHidden size={22} />
      <span className="pulse-dot" />
    </div>
  );
}
