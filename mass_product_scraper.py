import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
import json
import sqlite3
from deep_product_scraper_v4 import deep_scrape_final
from rotate_vpn import rotate_mullvad

async def mass_scrape_turbo(concurrency=3, vpn_rotate_every=30):
    # 1. Caricamento e Deduplicazione Link (Solo Base URL)
    with open("fluidra_product_links_map.json", "r", encoding="utf-8") as f:
        map_data = json.load(f)
    
    all_links = set()
    for links in map_data.values():
        for l in links:
            all_links.add(l.split('?')[0]) # Prendiamo solo il base URL
    
    unique_links = sorted(list(all_links))
    
    # 2. Controllo DB
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM products WHERE url IS NOT NULL")
    done_urls = set(row[0].split('?')[0] for row in cursor.fetchall())
    
    todo_links = [l for l in unique_links if l not in done_urls]
    
    print(f"🚀 AVVIO SCRAPER TURBO (Concorrenza: {concurrency})")
    print(f"📦 Prodotti unici base: {len(unique_links)}")
    print(f"✅ Già fatti: {len(done_urls)}")
    print(f"⏳ Rimanenti: {len(todo_links)}")
    
    if not todo_links:
        print("🎉 Tutto completato!")
        return

    # Dividiamo in blocchi per la rotazione VPN
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        
        async def launch_browser():
            print("🌐 Lancio Browser Master...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
            )
            return context

        browser_context = await launch_browser()
        semaphore = asyncio.Semaphore(concurrency)
        processed_count = 0
        
        async def worker(url):
            nonlocal processed_count
            async with semaphore:
                # Creiamo una nuova pagina per ogni worker
                page = await browser_context.new_page()
                await Stealth().apply_stealth_async(page)
                try:
                    await deep_scrape_final(page, url, conn)
                    processed_count += 1
                except Exception as e:
                    print(f"⚠️ Errore su {url}: {e}")
                finally:
                    await page.close()

        # Cicliamo sui link a gruppi di 30 per gestire la rotazione VPN
        for i in range(0, len(todo_links), vpn_rotate_every):
            batch = todo_links[i:i+vpn_rotate_every]
            print(f"\n🌀 Elaborazione blocco {i//vpn_rotate_every + 1} ({len(batch)} prodotti)...")
            
            tasks = [worker(url) for url in batch]
            await asyncio.gather(*tasks)
            
            # Fine batch: Rotazione VPN
            if i + vpn_rotate_every < len(todo_links):
                print("\n🔄 Rotazione VPN Mullvad in corso...")
                await browser_context.close()
                rotate_mullvad()
                await asyncio.sleep(15)
                browser_context = await launch_browser()

        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    # Con 3 schede parallele e link puliti, triplichiamo la velocità
    asyncio.run(mass_scrape_turbo(concurrency=3))
