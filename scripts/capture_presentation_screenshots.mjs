/**
 * Capture des captures d'écran originales pour la présentation NASA Space Apps.
 *
 * Pilotage de Edge (système) via playwright-core (aucun navigateur Playwright
 * n'est installé sur cette machine). Les vues capturées affichent des données
 * RÉELLES : artefacts /artifacts/*.json, jobs API, couche risque calibrée.
 *
 * Usage  : node scripts/capture_presentation_screenshots.mjs
 * Prérequis : API (8010), frontend Vite (5176), web Vite (5173) démarrés.
 * Sortie : deliverables/screenshots/*.png
 */

import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "C:/Users/HP/Documents/GitHub/camtel-stockflow/frontend/node_modules/playwright-core"
);

const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const FRONTEND = "http://localhost:5176";
const WEBMON = "http://localhost:5173/fire-monitor.html";
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(REPO, "deliverables", "screenshots");

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** Attend qu'un texte apparaisse dans la page (insensible à la casse — CSS uppercase). */
async function waitForText(page, text, timeout = 20000) {
  await page.waitForFunction(
    (t) => (document.body.innerText || "").toUpperCase().includes(t.toUpperCase()),
    text,
    { timeout }
  );
}

/** Attend que les tuiles satellite soient chargées (fond propre). */
async function waitForTiles(page, min = 6, timeout = 30000) {
  await page
    .waitForFunction(
      (n) => document.querySelectorAll(".leaflet-tile-loaded").length >= n,
      min,
      { timeout }
    )
    .catch(() => {});
  await wait(3000);
}

/** Recherche « Cameroon » dans la barre du haut → vol vers la zone à zoom 8. */
async function flyToCameroon(page) {
  await page.fill("#searchInput", "Cameroon");
  await page.press("#searchInput", "Enter");
  await waitForText(page, "Location found", 15000).catch(() => {});
  await wait(4000); // géocodage Nominatim + flyTo + tuiles
  await waitForTiles(page, 8);
}

/** Clique un bouton du dock (frontend React) via son libellé anglais. */
async function dock(page, label) {
  await page.click(`nav.dock .navbtn:has-text("${label}")`);
}

async function main() {
  await mkdir(OUT, { recursive: true });

  const browser = await chromium.launch({ executablePath: EDGE, headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1600, height: 900 },
    deviceScaleFactor: 2,
    locale: "en-US",
  });
  const page = await ctx.newPage();
  const shot = async (name) => {
    await page.screenshot({ path: path.join(OUT, name) });
    console.log("✓", name);
  };

  /* 01 — Carte : couche risque + hotspots GIBS/FIRMS sur le Cameroun */
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".leaflet-tile", { timeout: 20000, state: "attached" });
  await flyToCameroon(page);
  await page.mouse.click(800, 450); // popup d'une cellule de risque (provenance)
  await wait(1200);
  await shot("01_map_risk.png");

  /* 02 — Comparaison de capteurs : détail d'une expérience réelle (Jaccard) */
  await page.goto(WEBMON, { waitUntil: "domcontentloaded" });
  await page.click('.navbtn[data-view="experiments"]');
  await page.waitForSelector('tr[data-job="11358097185b"]', { timeout: 20000 });
  await page.click('tr[data-job="11358097185b"]');
  await waitForText(page, "Jaccard (aggregate)", 25000);
  await waitForText(page, "Monthly divergences", 15000).catch(() => {});
  await wait(2500); // rendu du graphe mensuel
  await shot("02_sensor_comparison.png");

  /* 03 — Calendrier historique : divergences inter-capteurs par jour (API) */
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await dock(page, "Calendar");
  await waitForText(page, "Fire calendar");
  await waitForText(page, "December", 20000).catch(() => {});
  await wait(2500);
  await shot("03_historical_calendar.png");

  /* 04 — Modèle de risque : panneau configurant + métriques de backtest */
  await dock(page, "Risk");
  await waitForText(page, "Model metrics", 25000);
  await flyToCameroon(page); // fond satellite propre derrière le panneau
  await page.fill("#rpDate", "2020-12-31").catch(() => {}); // date = période du backtest
  await page.$eval("aside", (el) => { el.scrollTop = el.scrollHeight; }).catch(() => {});
  await wait(1500);
  await shot("04_risk_model.png");

  /* 05 — Jobs : expériences d'harmonisation réelles dans l'API */
  await page.keyboard.press("Escape"); // ferme le panneau risque
  await dock(page, "Jobs");
  await waitForText(page, "11358097185b", 25000);
  await wait(1500);
  await shot("05_jobs_dashboard.png");

  /* 06 — Qualité des données : artefact audit.json (1 170 fichiers) */
  await dock(page, "Quality");
  await waitForText(page, "Data quality report", 25000);
  await waitForText(page, "Files audited", 15000).catch(() => {});
  await wait(1200);
  await shot("06_data_quality.png");

  await browser.close();
  console.log("Done →", OUT);
}

main().catch((e) => {
  console.error("FAILED:", e.message);
  process.exit(1);
});
