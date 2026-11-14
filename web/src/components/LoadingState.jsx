/**
 * LoadingState - Component for displaying loading state
 * Used by: All modules
 * 
 * @param {string} message - Optional loading message
 */
export default function LoadingState({ message = "Chargement…" }) {
  return (
    <div className="loading">
      {message}
    </div>
  );
}
