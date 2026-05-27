import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def inspect_discontinued(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"Ispezionando prodotto fuori produzione: {url}")
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(10)
        
        content = await page.content()
        with open("discontinued_debug.html", "w", encoding="utf-8") as f:
            f.write(content)
        
        await page.screenshot(path="discontinued_check.png")
        print("Analisi completata. HTML salvato in discontinued_debug.html")
        
        # Cerchiamo la parola "produzione" nel testo visibile
        found = "fuori produzione" in content.lower() or "discontinued" in content.lower()
        print(f"Dicitura trovata nel codice: {found}")
        
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(inspect_discontinued("https://pro.fluidra.com/it_it/1128401-pressacavo-faro-pu9.html"))
