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

  return { loading, error, getFireRisk, chat, geocode };
}
