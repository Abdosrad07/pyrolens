/**
 * Chargement de l'artefact fire_risk.json.
 * Essaie /artifacts/fire_risk.json puis /api/v1/fire-risk.
 */

import { apiGet } from "./api.js";

export async function fetchFireRisk() {
  const urls = ["/artifacts/fire_risk.json", "/api/v1/fire-risk"];
  for (const url of urls) {
    try {
      const data = await apiGet(url);
      if (data && data.cells) return data;
    } catch (_) {
      // essayer la suivante
    }
  }
  return null;
}
