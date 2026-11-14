/**
 * TopBar — barre du haut : marque, recherche, actions.
 *
 * Props:
 *  - onSearch: (query: string) => void
 *  - onOpenMenu: () => void
 *  - onOpenRisk: () => void
 *  - onOpenAi: () => void
 *  - onAnnounce: () => void
 *  - onContact: () => void
 */

import { useState } from "react";
import Icons from "./icons.jsx";

export default function TopBar({ onSearch, onOpenMenu, onOpenRisk, onOpenAi, onAnnounce, onContact }) {
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (!q || busy) return;
    setBusy(true);
    await onSearch?.(q);
    setBusy(false);
  };

  return (
    <header className="topbar">
      <div className="brand">
        <span className="mark">
          <Icons name="flame" className="ic" ariaHidden size={22} />
        </span>
        <div>
          <h1>Fire Monitor</h1>
          <small>Feux actifs · données NASA FIRMS</small>
        </div>
      </div>
      <span className="sp" />
      <form className="search-form" role="search" onSubmit={handleSubmit}>
        <Icons name="search" className="ic" ariaHidden size={18} />
        <label className="sr-only" htmlFor="searchInput">Rechercher un lieu</label>
        <input
          id="searchInput"
          type="search"
          placeholder="Rechercher un lieu…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
          enterKeyHint="search"
        />
        <button type="submit" disabled={busy}>Aller</button>
      </form>
      <button className="ibtn btn-search" type="button" title="Rechercher un lieu" aria-label="Rechercher un lieu" onClick={onOpenMenu}>
        <Icons name="search" className="ic" ariaHidden size={18} />
      </button>
      <button className="ibtn" type="button" title="Annonces" aria-label="Annonces" onClick={onAnnounce}>
        <Icons name="megaphone" className="ic" ariaHidden size={18} />
      </button>
      <button className="ibtn" type="button" title="Contacter la NASA Earthdata" aria-label="Contact" onClick={onContact}>
        <Icons name="chat" className="ic" ariaHidden size={18} />
      </button>
      <button className="ibtn" type="button" title="Ouvrir le menu principal" aria-label="Ouvrir le menu principal" onClick={onOpenMenu}>
        <Icons name="menu" className="ic" ariaHidden size={18} />
      </button>
    </header>
  );
}
