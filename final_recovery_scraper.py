import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
import json
import sqlite3
from deep_product_scraper_v4 import deep_scrape_final
from rotate_vpn import rotate_mullvad

async def final_recovery(concurrency=3, vpn_rotate_every=20):
    # 1. Caricamento Link Orfani
    if not os.path.exists("missing_links.json"):
        print("❌ File missing_links.json non trovato.")
        return
        
    todo_links = json.load(open("missing_links.json", "r"))
    print(f"🚀 AVVIO RECUPERO FINALE: {len(todo_links)} link orfani.")
    
    if not todo_links:
        print("✅ Tutti i prodotti sono completi!")
        return

    conn = sqlite3.connect('fluidra_catalog.db')

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        
        async def launch_browser():
            print("🌐 Lancio Browser Master...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir, headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            return context

        browser_context = await launch_browser()
        semaphore = asyncio.Semaphore(concurrency)
        
        async def worker(url):
            async with semaphore:
                page = await browser_context.new_page()
                await Stealth().apply_stealth_async(page)
                try:
                    await deep_scrape_final(page, url, conn)
                except Exception as e:
                    print(f"⚠️ Errore residuo su {url}: {e}")
                finally:
                    await page.close()

        # Cicliamo a blocchi per VPN
        for i in range(0, len(todo_links), vpn_rotate_every):
            batch = todo_links[i:i+vpn_rotate_every]
            print(f"\n🌀 Elaborazione blocco orfani {i//vpn_rotate_every + 1}...")
            
            tasks = [worker(url) for url in batch]
            await asyncio.gather(*tasks)
            
            if i + vpn_rotate_every < len(todo_links):
                print("\n🔄 Rotazione VPN Mullvad...")
                await browser_context.close()
                rotate_mullvad()
                await asyncio.sleep(15)
                browser_context = await launch_browser()

        await browser_context.close()
    conn.close()
    print("\n🏁 RECUPERO COMPLETATO!")

if __name__ == "__main__":
    asyncio.run(final_recovery())
