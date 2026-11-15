/**
 * AiPanel — panneau latéral de l'assistant IA.
 *
 * Props: { open: boolean, onClose: () => void, onSend: (q: string) => Promise<string|null> }
 * State interne : messages, input, busy.
 */

import { useState, useEffect, useRef } from "react";
import { useI18n } from "../i18n/index.jsx";
import Icons from "../components/icons.jsx";

export default function AiPanel({ open, onClose, onSend }) {
  const { t } = useI18n();
  const [messages, setMessages] = useState([
    { role: "bot", text: t("ai.welcome") },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef(null);

  useEffect(() => {
    if (open) logRef.current?.scrollTo(0, logRef.current.scrollHeight);
  }, [messages, open]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    const reply = await onSend(q);
    setBusy(false);
    if (reply) setMessages((m) => [...m, { role: "bot", text: reply }]);
    else setMessages((m) => [...m, { role: "bot", text: t("ai.notConnected", "Assistant non connecté : le backend /api/v1/chat est requis."), cls: "err" }]);
  };

  const suggestions = [
    t("ai.suggestions.summarize"),
    t("ai.suggestions.colors"),
    t("ai.suggestions.modisViirs"),
  ];

  return (
    <aside
      id="aiPanel"
      className={`ai-panel${open ? " open" : ""}`}
      aria-label="Assistant IA"
      aria-hidden={!open}
    >
      <div className="rp-head">
        <Icons name="spark" className="ic" ariaHidden size={18} />
        <h2>{t("ai.title", "Assistant IA")}</h2>
        <button className="ibtn" type="button" title={t("ai.newChat")} aria-label={t("ai.newChat")}
          onClick={() => setMessages([{ role: "bot", text: t("ai.welcomeNew") }])}
        >
          <Icons name="plus" className="ic" ariaHidden size={18} />
        </button>
        <button className="ibtn" type="button" title="Fermer" aria-label="Fermer l'assistant" onClick={onClose}>
          <Icons name="x" className="ic" ariaHidden size={18} />
        </button>
      </div>

      <div className="ai-log" ref={logRef} role="log" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={`ai-msg ${m.role}${m.cls ? " " + m.cls : ""}`}>
            {m.text}
          </div>
        ))}
        {busy && <div className="ai-msg bot typing">{t("ai.thinking", "Réflexion en cours…")}</div>}
      </div>

      <div className="ai-suggest" style={{ display: messages.length <= 1 ? "flex" : "none" }}>
        {suggestions.map((s) => (
          <button key={s} type="button" onClick={() => setInput(s)}>{s}</button>
        ))}
      </div>

      <form className="ai-form" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="aiInput">Votre question</label>
        <textarea
          id="aiInput"
          rows={1}
          placeholder={t("ai.placeholder", "Posez votre question…")}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); handleSubmit(e); }
          }}
        />
        <button className="ai-send" type="submit" aria-label={t("ai.send", "Envoyer")} disabled={busy || !input.trim()}>
          <Icons name="send" className="ic" ariaHidden size={18} />
        </button>
      </form>

      <p className="ai-note">
        Réponses générées par IA, à vérifier. Ce n&apos;est pas une alerte incendie.
      </p>
    </aside>
  );
}
