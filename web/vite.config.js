import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Freebuff injecte PORT ; liaison 0.0.0.0 obligatoire, HMR conservé désactivé.
const port = Number(process.env.PORT || 5173);
const proxy = { "/api": { target: "", changeOrigin: true } };

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  // Cible du proxy /api → backend FastAPI : PYROLENS_API_ORIGIN (env shell ou
  // .env/.env.local), défaut http://localhost:8000.
  proxy["/api"].target =
    env.PYROLENS_API_ORIGIN || process.env.PYROLENS_API_ORIGIN || "http://localhost:8000";
  // Mode API : en `vite dev`, VITE_API_BASE vaut "" par défaut → appels
  // /api/v1 same-origin relayés par le proxy (pas de CORS). Un .env(.local)
  // peut surcharger avec une URL absolue. En `vite build`, la variable reste
  // indéfinie → mode statique (/artifacts) préservé par défaut.
  const apiBase =
    env.VITE_API_BASE ?? (command === "serve" ? "" : undefined);
  const define =
    apiBase !== undefined
      ? { "import.meta.env.VITE_API_BASE": JSON.stringify(apiBase) }
      : {};

  return {
    plugins: [react()],
    define,
    server: {
      host: "0.0.0.0",
      port,
      strictPort: false,
      hmr: false,
      // L'aperçu Freebuff est servi sous un sous-domaine isolé : l'accepter.
      allowedHosts: true,
      proxy,
    },
    preview: {
      host: "0.0.0.0",
      port,
      hmr: false,
      allowedHosts: true,
      proxy,
    },
  };
});
