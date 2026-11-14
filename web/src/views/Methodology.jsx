/**
 * Methodology - View for scientific methodology documentation
 */
import { useState, useEffect } from "react";
import { loadMethodology } from "../data.js";
import LoadingState from "../components/LoadingState.jsx";
import ErrorState from "../components/ErrorState.jsx";

export default function Methodology() {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    loadMethodology()
      .then((result) => {
        if (alive) {
          setContent(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (alive) {
          setError(err);
          setLoading(false);
        }
      });
    return () => {
      alive = false;
    };
  }, []);

  if (loading) {
    return (
      <div>
        <h2 className="page-title">Méthodologie</h2>
        <p className="page-sub">
          Documentation scientifique des méthodes utilisées dans PyroLens.
        </p>
        <div className="panel">
          <LoadingState message="Chargement de la méthodologie…" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="page-title">Méthodologie</h2>
        <p className="page-sub">
          Documentation scientifique des méthodes utilisées dans PyroLens.
        </p>
        <ErrorState error={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  return (
    <div>
      <h2 className="page-title">Méthodologie</h2>
      <p className="page-sub">
        Documentation scientifique des méthodes utilisées dans PyroLens.
      </p>
      <div className="panel" style={{ padding: "24px" }}>
        <div
          dangerouslySetInnerHTML={{
            __html: content
              ? content
                  .replace(/^# /gm, '<h1>')
                  .replace(/^## /gm, '<h2>')
                  .replace(/^### /gm, '<h3>')
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br>')
              : "Contenu non disponible",
          }}
          style={{ lineHeight: "1.6" }}
        />
      </div>
    </div>
  );
}
