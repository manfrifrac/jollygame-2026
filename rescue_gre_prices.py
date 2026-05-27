import asyncio
import sqlite3
import json
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

async def rescue_gre_prices():
    db_path = "fluidra_clean.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prendiamo i prodotti Gre (hanno taxonomy 'Piscine in Acciaio > Gre' o URL grepool)
    cursor.execute("SELECT sku, url FROM products WHERE url LIKE '%grepool.com%'")
    targets = cursor.fetchall()
    
    print(f"🚀 Recupero prezzi per {len(targets)} prodotti Gre...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        updates = 0
        for sku, url in targets:
            try:
                await page.goto(url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                # Cerchiamo il prezzo nel formato "Acquista da 1234 €"
                match = re.search(r'Acquista da\s*([\d.]+)\s*€', content)
                if not match:
                    # Fallback: cerchiamo qualsiasi cifra seguita da €
                    match = re.search(r'([\d.]+)\s*€', content)
                
                if match:
                    price_str = match.group(1).replace('.', '')
                    price = float(price_str)
                    cursor.execute("UPDATE products SET price_list = ? WHERE sku = ?", (price, sku))
                    updates += 1
                    print(f"   💰 SKU {sku}: Prezzo trovato -> {price} €")
                else:
                    print(f"   ❌ SKU {sku}: Prezzo non trovato")
                
                if updates % 10 == 0: conn.commit()
                
            except Exception as e:
                print(f"   ⚠️ Errore su {sku}: {e}")
                
        conn.commit()
        await browser.close()
    
    conn.close()
    print(f"\n✅ Aggiornati {updates} prezzi Gre.")

if __name__ == "__main__":
    asyncio.run(rescue_gre_prices())
