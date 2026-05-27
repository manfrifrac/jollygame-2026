import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def find_urls():
    with open("gre_mapped_drafts.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    missing = [p for p in products if not p['gre_url'] and p['sku']]
    print(f"🔍 Ricerca URL per {len(missing)} prodotti via SKU...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        for prod in missing:
            sku = prod['sku']
            search_url = f"https://www.grepool.com/it/ricerca?q={sku}"
            print(f"🔎 Cerco SKU {sku} -> {search_url}")
            
            try:
                await page.goto(search_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # Vediamo se ci sono risultati
                # Spesso Grepool reindirizza direttamente al prodotto se lo SKU è univoco
                current_url = page.url
                if "ricerca" not in current_url and "grepool.com" in current_url:
                    print(f"   ✅ Trovato (Redirect): {current_url}")
                    prod['gre_url'] = current_url
                else:
                    # Cerca il primo link al prodotto nei risultati
                    try:
                        first_link = await page.locator(".product-item a, .product-list a, a.product-name").first.get_attribute("href")
                        if first_link:
                            full_url = first_link if first_link.startswith("http") else f"https://www.grepool.com{first_link}"
                            print(f"   ✅ Trovato (Link): {full_url}")
                            prod['gre_url'] = full_url
                        else:
                            print(f"   ❌ Non trovato.")
                    except:
                        print(f"   ❌ Non trovato (locator failed).")
            except Exception as e:
                print(f"   ❌ Errore: {e}")
        
        await browser.close()

    with open("gre_mapped_drafts_final.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    
    print("\n✅ Mappatura finale salvata.")

if __name__ == "__main__":
    asyncio.run(find_urls())
