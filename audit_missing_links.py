import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import sqlite3
import os

async def check_missing_links():
    # Carica link totali
    with open("fluidra_product_links_map.json", "r", encoding="utf-8") as f:
        map_data = json.load(f)
    all_links = set()
    for links in map_data.values():
        for l in links:
            all_links.add(l.split('?')[0])
    
    # Carica link fatti
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM products WHERE url IS NOT NULL AND is_spare_part=0")
    done_links = set(row[0].split('?')[0] for row in cursor.fetchall())
    conn.close()
    
    missing = [l for l in all_links if l not in done_links]
    print(f"🔍 Analisi di {len(missing)} link mancanti...")
    
    if not missing:
        print("✅ Nessun link mancante!")
        return

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        results = []
        # Testiamo i primi 20 link mancanti per capire il pattern
        for url in missing[:20]:
            try:
                response = await page.goto(url, wait_until="load", timeout=30000)
                status = response.status if response else "No Response"
                print(f"URL: {url} -> Status: {status}")
                results.append({"url": url, "status": status})
            except Exception as e:
                print(f"URL: {url} -> Errore: {str(e)[:50]}")
                results.append({"url": url, "status": "Error", "error": str(e)[:50]})
        
        await browser_context.close()
    
    with open("missing_links_audit.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(check_missing_links())
