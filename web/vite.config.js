import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Freebuff injecte PORT ; liaison 0.0.0.0 obligatoire, HMR conservé désactivé.
const port = Number(process.env.PORT || 5173);

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port,
    strictPort: false,
    hmr: false,
    // L'aperçu Freebuff est servi sous un sous-domaine isolé : l'accepter.
    allowedHosts: true,
  },
  preview: {
    host: "0.0.0.0",
    port,
    hmr: false,
    allowedHosts: true,
  },
});
