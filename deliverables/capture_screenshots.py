"""
Capture authentiques des vues de l'application PyroLens.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:5174"
CHROMIUM = r"C:\Users\USER\AppData\Local\ms-playwright\chromium-1255\chrome-win64\chrome.exe"

# Le dock est le seul sélecteur de navigation
# Chaque bouton a une classe .navbtn et un span.lbl avec le label
SHOTS = [
    # (filename, CSS selector par index dans le dock, wait, description)
    ("01_map_risk.png",           "map",      5000, "Carte + couche risque"),
    ("02_sensor_comparison.png", "overview",  3000, "Vue Aperçu"),
    ("03_historical_calendar.png","calendar", 3000, "Calendrier"),
    ("04_risk_model.png",        "risk",      3000, "Panels risque"),
    ("05_jobs_dashboard.png",    "jobs",      3000, "Jobs"),
    ("06_data_quality.png",      "quality",   3000, "Qualité données"),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM)
        ctx = await browser.new_context(viewport={"width":1440,"height":900}, device_scale_factor=2)
        page = await ctx.new_page()

        # 1. Charger la page (carte par défaut)
        print("Chargement de la page...")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(5000)

        for fname, view_id, wait, desc in SHOTS:
            try:
                if view_id == "map":
                    # Déjà sur la carte
                    pass
                else:
                    # Retourner à la carte d'abord
                    map_btn = page.locator(".dock .navbtn", has_text="Map")
                    await map_btn.first.click()
                    await page.wait_for_timeout(2000)

                    # Cliquer la vue voulue
                    btn = page.locator(f".dock .navbtn:has-text('{view_id.capitalize()}')").first
                    await btn.click()

                await page.wait_for_timeout(wait)
                out = OUT / fname
                await page.screenshot(path=str(out))
                print(f"OK  {fname} ({out.stat().st_size:,} B) [{desc}]")
            except Exception as e:
                print(f"ERR {fname}: {e}")

        await ctx.close()
        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
