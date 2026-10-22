// Worker Freebuff Sites : sert le build statique Vite (web/dist), y compris
// les artefacts JSON/PNG du pipeline Python sous /artifacts/.
export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
