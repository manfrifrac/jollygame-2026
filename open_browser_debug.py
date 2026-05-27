import asyncio
from playwright.async_api import async_playwright
import os

async def open_browser():
    async with async_playwright() as p:
        # Usiamo la cartella locale del progetto
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        
        print(f"Apertura browser VISIBILE con profilo locale: {user_data_dir}")
        
        try:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False, # VISIBILE
                args=["--disable-blink-features=AutomationControlled"],
                slow_mo=100
            )
            
            page = browser_context.pages[0]
            print("Navigazione verso Fluidra Pro...")
            await page.goto("https://pro.fluidra.com/it_it/", wait_until="load")
            
            print("\n>>> IL BROWSER È APERTO <<<")
            print("Per favore, effettua il login manualmente se non sei loggato.")
            print("Una volta fatto, la sessione verrà salvata in questa cartella.")
            print("Lo script rimarrà aperto per 5 minuti. Chiudi il browser quando hai finito.")
            
            await asyncio.sleep(300) 
            
        except Exception as e:
            print(f"\nErrore: {e}")
        finally:
            if 'browser_context' in locals():
                await browser_context.close()

if __name__ == "__main__":
    asyncio.run(open_browser())
