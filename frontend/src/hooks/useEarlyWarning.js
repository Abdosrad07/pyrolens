/**
 * useEarlyWarning — chargement des données du Early Warning Center.
 *
 * Sépare le fetch (service earlyWarning.js) de la UI.
 * Gère les états : loading / data / error / empty / mock.
 *
 * Retourne {
 *   loading, error,
 *   summary,            // résumé (KPI) ou null
 *   alerts,             // array d'alertes ou []
 *   selected, select,  // alerte sélectionnée + setter
 *   usingMock,          // true si on est sur le fixture
 *   reload,
 * }
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import useEwFactory from "../services/earlyWarning.js";

export default function useEarlyWarning() {
  // useMemo stabilise l'objet service (la factory crée un nouvel objet à chaque render)
  const ew = useMemo(() => useEwFactory(), []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [usingMock, setUsingMock] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, a] = await Promise.all([ew.summary(), ew.alerts()]);
      setSummary(s);
      setAlerts(a?.items || []);
      setUsingMock(ew.usingMock());
    } catch (e) {
      setError(e.message);
      setSummary(null);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [ew]);

  useEffect(() => { load(); }, [load]);

  // Tri par défaut : sévérité décroissante (critical > high > moderate > low)
  const SEV_RANK = { critical: 0, high: 1, moderate: 2, low: 3 };
  const sorted = useMemo(
    () => [...alerts].sort((x, y) => SEV_RANK[x.severity] - SEV_RANK[y.severity] || (y.recent_detections || 0) - (x.recent_detections || 0)),
    [alerts]
  );

  return {
    loading,
    error,
    summary,
    alerts,
    sorted,
    selected,
    select: setSelected,
    usingMock,
    reload: load,
  };
}
