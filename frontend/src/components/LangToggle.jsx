/**
 * LangToggle — bouton de bascule FR / EN.
 */

import Icons from "./icons.jsx";
import { useI18n } from "../i18n/index.jsx";

export default function LangToggle() {
  const { lang, toggle, t } = useI18n();

  return (
    <button
      className="ibtn lang-toggle"
      type="button"
      title={t("lang.fr")}
      aria-label={t("lang.en")}
      onClick={toggle}
      style={{
        height: "2.4rem",
        padding: "0 .55rem",
        display: "inline-flex",
        alignItems: "center",
        gap: ".35rem",
        borderRadius: ".7rem",
        color: "#E4EEEA",
        fontWeight: 700,
        fontSize: ".8rem",
        letterSpacing: ".04em",
        background: "rgb(255 255 255/.08)",
        border: "1.5px solid rgb(255 255 255/.18)",
        lineHeight: 1,
        transition: "background .15s, border-color .15s",
      }}
    >
      <Icons name="globe" ariaHidden size={16} />
      <span aria-hidden="true">{lang.toUpperCase()}</span>
    </button>
  );
}
