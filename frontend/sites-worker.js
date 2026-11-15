// Worker Freebuff Sites : sert le build statique Vite (frontend/dist) en SPA.
// Les appels /api/* partent vers VITE_API_BASE (backend séparé) — pas de proxy ici.
export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
