/**
 * ErrorState - Component for displaying error state
 * Used by: All modules
 * 
 * @param {Error|string} error - Error object or message
 * @param {function} onRetry - Optional retry callback
 * @param {string} details - Optional technical details
 */
export default function ErrorState({ error, onRetry, details }) {
  const errorMessage = error instanceof Error ? error.message : String(error);

  return (
    <div className="panel">
      <div className="banner warn">
        <strong>Erreur</strong>
        {errorMessage}
      </div>
      {details && (
        <details style={{ marginTop: "12px" }}>
          <summary className="linkish">Détails techniques</summary>
          <pre style={{ marginTop: "8px", fontSize: "12px", color: "var(--muted)" }}>
            {details}
          </pre>
        </details>
      )}
      {onRetry && (
        <button className="btn" onClick={onRetry} style={{ marginTop: "12px" }}>
          Réessayer
        </button>
      )}
    </div>
  );
}
