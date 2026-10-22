import { useState } from "react";

/**
 * Écran d'authentification — version factice (aucun backend de comptes).
 * La session de démonstration est un simple indicateur côté client
 * (sessionStorage) : aucun identifiant n'est transmis ni stocké.
 * La branche réelle (comptes, jetons, `PYROLENS_API_TOKEN` côté API) sera
 * branchée ici sans changer l'interface.
 */
export default function Auth({ returnTo, onAuthed, onCancel, onDemo }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function submit(e) {
    e.preventDefault();
    if (!email.includes("@") || password.length < 4) {
      setError("Saisissez un e-mail valide et un mot de passe d'au moins 4 caractères.");
      return;
    }
    onAuthed(returnTo);
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="brand" style={{ marginBottom: 14 }}>
          <h1>PyroLens</h1>
          <div className="sub">Session tableau de bord</div>
        </div>

        <h2 className="auth-title">Se connecter</h2>
        <p className="muted small" style={{ marginTop: 0 }}>
          {returnTo && returnTo !== "overview" ? (
            <>
              Vous serez redirigé vers <strong>{returnTo}</strong> après connexion.
            </>
          ) : (
            "Accès au tableau de bord et à l'historique des exécutions."
          )}
        </p>

        <form className="auth-form" onSubmit={submit}>
          <label htmlFor="auth-email">E-mail</label>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            placeholder="vous@exemple.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <label htmlFor="auth-password">Mot de passe</label>
          <input
            id="auth-password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <div className="auth-error">{error}</div>}

          <button className="btn primary block" type="submit">
            Se connecter
          </button>
        </form>

        <div className="auth-alt">
          <button className="btn ghost block" onClick={onDemo}>
            Continuer sans compte → démo
          </button>
        </div>

        <p className="muted small">
          Version de démonstration : la connexion est simulée dans le navigateur.
          Les comptes réels seront gérés par l'API PyroLens (jeton
          <code> PYROLENS_API_TOKEN</code>), sans changer cet écran.
        </p>

        <button className="auth-back" onClick={onCancel}>
          ← Retour à l'accueil
        </button>
      </div>
    </div>
  );
}
