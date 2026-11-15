/**
 * useApi — hook utilitaire pour interroger l'API Fire Monitor.
 *
 * Fournit des helpers typés pour :
 *  - /api/v1/fire-risk (données risque)
 *  - /api/v1/chat (IA)
 *  - recherche Nominatim (géocodage)
 */

import { useState, useCallback } from "react";
import { apiGet, apiPost } from "../services/api.js";

export default function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getFireRisk = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      return await apiGet("/api/v1/fire-risk");
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const chat = useCallback(async (messages, context) => {
    setLoading(true);
    setError(null);
    try {
      const j = await apiPost("/api/v1/chat", { messages, context });
      return j.reply || j.message || j.content || null;
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Lance un entraînement predict (job async — ~10 min sur données réelles). */
  const predict = useCallback(async ({ grid_deg = 0.25, window = 8, reference_date = null }) => {
    return apiPost("/api/v1/predict", { grid_deg, window, reference_date });
  }, []);

  const getPredictJob = useCallback(async (jobId) => {
    return apiGet(`/api/v1/predict/${jobId}`);
  }, []);

  /** Liste tous les jobs (harmonization, firms_analyze, firms_history, predict). */
  const listJobs = useCallback(async () => {
    return apiGet("/api/v1/experiments");
  }, []);

  /** Série quotidienne du calendrier des feux (vraies données pipeline). */
  const fireCalendarDaily = useCallback(async ({ pair, start, end, limit = 20000 } = {}) => {
    const q = new URLSearchParams();
    if (pair) q.set("pair", pair);
    if (start) q.set("start", start);
    if (end) q.set("end", end);
    q.set("limit", String(limit));
    return apiGet(`/api/v1/fire-calendar/daily?${q}`);
  }, []);

  const geocode = useCallback(async (q) => {
    try {
      const r = await fetch(
        "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" +
          encodeURIComponent(q)
      );
      const j = await r.json();
      return j[0] ? { lat: +j[0].lat, lon: +j[0].lon } : null;
    } catch {
      return null;
    }
  }, []);

  return { loading, error, getFireRisk, chat, predict, getPredictJob, listJobs, fireCalendarDaily, geocode };
}
