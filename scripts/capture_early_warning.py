"""
Capture l'interface Early Warning Center pour validation visuelle.
Nécessite le dev server Vite sur :8800 (ou PORT param).
"""
import sys
import asyncio
from playwright.async_api import async_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "5188"
OUT = "early_warning_check.png"
W, H = 1440, 1000


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": W, "height": H})
        await page.goto(f"http://localhost:{PORT}/", wait_until="networkidle")
        await page.wait_for_timeout(1500)

        # Cliquer sur le bouton "Pré-alerte" du DockNav (icône alert)
        # Le bouton porte l'aria-label / le libellé via i18n : "Pré-alerte"
        clicked = False
        for label in ["Pré-alerte", "Early warning", "Pré-alerte"]:
            try:
                btn = page.get_by_role("button", name=label)
                if await btn.count():
                    await btn.first.click()
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            # Fallback : clic sur le bouton avec title=Pré-alerte
            try:
                await page.click('button[title="Pré-alerte"]')
                clicked = True
            except Exception:
                pass

        await page.wait_for_timeout(2500)  # chargement mock + cartes

        # Cliquer la 1re alerte pour voir les détails + chart
        try:
            row = page.locator('table.jl tbody tr').first
            if await row.count():
                await row.click()
                await page.wait_for_timeout(800)
        except Exception:
            pass

        await page.screenshot(path=OUT, full_page=False)
        print(f"capture -> {OUT} (clicked dock: {clicked})")
        await b.close()


asyncio.run(main())
