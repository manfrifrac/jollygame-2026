import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup
import json
import sqlite3

async def test_bestway_data_quality():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Test su un prodotto complesso: Idromassaggio (solitamente ha molte specifiche)
        test_url = "https://it.bestway.eu/p/idromassaggio-gonfiabile-lay-z-spa-mauritius-airjet-5-7-persone-con-app"
        print(f"Test qualità dati su: {test_url}")
        
        page = await browser_context.new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto(test_url, wait_until="networkidle")
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if next_data_script:
            pj = json.loads(next_data_script.string)
            prod = pj.get("props", {}).get("pageProps", {}).get("product", {})
            
            print("\n--- RISULTATI TEST QUALITÀ ---")
            print(f"Titolo: {prod.get('name')}")
            print(f"SKU: {prod.get('sku')}")
            print(f"EAN: {prod.get('ean')}")
            print(f"Categoria: {' > '.join(prod.get('categories', []))}")
            
            # Controllo Specifiche Tecniche
            specs = {k: v for k, v in prod.items() if isinstance(v, (str, int, float)) and k not in ['name', 'descriptionHtml', 'bulletPoints', 'path', 'slug', 'id', 'bigcommerceId']}
            print(f"\nSpecifiche Tecniche trovate ({len(specs)}):")
            for k, v in list(specs.items())[:10]: # Mostra prime 10
                print(f"  - {k}: {v}")
            
            # Controllo Immagini e Video
            imgs = [img.get("url") for img in prod.get("images", []) if img.get("url")]
            video = next((img.get("videoUrl") for img in prod.get("images", []) if img.get("videoUrl")), "Nessuno")
            print(f"\nImmagini: {len(imgs)} trovate")
            print(f"Video YouTube: {video}")
            
            # Controllo Descrizione
            desc = prod.get("descriptionHtml", "")
            print(f"Lunghezza Descrizione HTML: {len(desc)} caratteri")
            
            if prod.get('ean') and len(specs) > 5 and len(imgs) > 0:
                print("\n✅ TEST SUPERATO: I dati tecnici sono completi e pronti per il database.")
            else:
                print("\n⚠️ ATTENZIONE: Alcuni dati critici (EAN o Specs) potrebbero mancare.")
        
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(test_bestway_data_quality())
