/**
 * Toast — notification toast flottante.
 *
 * Props: { message: string | null, onDone: () => void }
 * Disparaît automatiquement après 2,6 s.
 */

import { useEffect } from "react";

export default function Toast({ message, onDone }) {
  useEffect(() => {
    if (!message) return;
    const t = setTimeout(onDone, 2600);
    return () => clearTimeout(t);
  }, [message, onDone]);

  return (
    <div className="toast" role="status" aria-live="polite">
      {message}
    </div>
  );
}
