/**
 * EmptyState - Component for displaying empty state
 * Used by: All modules
 * Important: Never use "pas de feu" - use "aucun_enregistrement" or similar
 * 
 * @param {string} message - Empty state message
 */
export default function EmptyState({ message = "Aucun enregistrement disponible" }) {
  return (
    <div className="panel" style={{ textAlign: "center", padding: "40px 20px" }}>
      <p className="muted">{message}</p>
    </div>
  );
}
