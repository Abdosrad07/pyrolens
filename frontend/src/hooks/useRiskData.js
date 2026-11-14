/**
 * useRiskData — hook pour charger et gérer les données de risque de feu.
 *
 * Charge fire_risk.json via src/services/fireRisk.js.
 * Retourne { riskData, loading, error, reload }.
 */

import { useState, useCallback } from "react";
import { fetchFireRisk } from "../services/fireRisk.js";

export default function useRiskData() {
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFireRisk();
      setRiskData(data);
    } catch (err) {
      setError(err.message);
      setRiskData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const metrics = riskData?.metrics || {};
  const cellsCount = (riskData?.cells || []).length;
  const highCells = (riskData?.cells || []).filter((c) => c.prob >= 0.6).length;
  const origin = riskData?.data_origin || "inconnue";
  const generatedAt = riskData?.generated_at
    ? new Date(riskData.generated_at).toLocaleDateString("fr-FR")
    : "?";

  return {
    riskData,
    loading,
    error,
    reload: load,
    metrics,
    cellsCount,
    highCells,
    origin,
    generatedAt,
  };
}
