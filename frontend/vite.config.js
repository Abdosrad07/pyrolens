import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// PyroLens sur port 5174 pour ne pas entrer en conflit avec web/ (5173).
// Le proxy /api relaye vers le backend FastAPI.
const port = Number(process.env.PORT || 5174);
const proxy = { "/api": { target: "", changeOrigin: true } };

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  proxy["/api"].target =
    env.VITE_API_ORIGIN ||
    process.env.VITE_API_ORIGIN ||
    "http://127.0.0.1:8010";

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
