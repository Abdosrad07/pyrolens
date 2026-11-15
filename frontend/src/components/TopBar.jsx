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
import { useI18n } from "../i18n/index.jsx";
import Icons from "./icons.jsx";
import LangToggle from "./LangToggle.jsx";

export default function TopBar({ onSearch, onOpenMenu, onOpenRisk, onOpenAi, onAnnounce, onContact, onToggleLang }) {
  const { t } = useI18n();
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
          <h1>{t("brand.title", "PyroLens")}</h1>
          <small>{t("brand.subtitle", "Feux actifs · données NASA FIRMS")}</small>
        </div>
      </div>
      <span className="sp" />
      <form className="search-form" role="search" onSubmit={handleSubmit}>
        <Icons name="search" className="ic" ariaHidden size={18} />
        <label className="sr-only" htmlFor="searchInput">{t("search.label")}</label>
        <input
          id="searchInput"
          type="search"
          placeholder={t("search.placeholder")}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
          enterKeyHint="search"
        />
        <button type="submit" disabled={busy}>{t("search.go")}</button>
      </form>
      <button className="ibtn btn-search" type="button" title={t("searchBtn")} aria-label={t("searchBtn")} onClick={onOpenMenu}>
        <Icons name="search" className="ic" ariaHidden size={18} />
      </button>
      <button className="ibtn" type="button" title={t("announcements")} aria-label={t("announcements")} onClick={onAnnounce}>
        <Icons name="megaphone" className="ic" ariaHidden size={18} />
      </button>
      <button className="ibtn" type="button" title={t("contact")} aria-label={t("contact")} onClick={onContact}>
        <Icons name="chat" className="ic" ariaHidden size={18} />
      </button>
      <button className="ibtn" type="button" title={t("menu")} aria-label={t("menu")} onClick={onOpenMenu}>
        <Icons name="menu" className="ic" ariaHidden size={18} />
      </button>
      <LangToggle />
    </header>
  );
}
