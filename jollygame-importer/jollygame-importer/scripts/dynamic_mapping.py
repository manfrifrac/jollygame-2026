import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import re

async def dynamic_mapping():
    # Carichiamo la mappatura v4 (che ha già i 7 URL sicuri)
    with open("gre_mapped_drafts_v4.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    missing = [p for p in products if not p['gre_url']]
    print(f"🔍 Tentativo di mappatura dinamica per {len(missing)} prodotti...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        for prod in missing:
            # 1. Prova ricerca per SKU se numerico, o Titolo se SKU null
            # Se lo SKU è numerico corto (4-6 cifre), spesso fallisce la ricerca su Grepool.
            # Proviamo a usare il titolo direttamente per una maggiore precisione commerciale.
            search_query = prod['title']
            print(f"\n🔎 Cerco Titolo: {search_query}")
            
            try:
                await page.goto(f"https://www.grepool.com/it/ricerca?q={search_query.replace(' ', '+')}", wait_until="load")
                await page.wait_for_timeout(3000)

                # Controllo Redirect Diretto
                if "ricerca" not in page.url and "grepool.com" in page.url:
                    print(f"   ✅ Trovato (Redirect): {page.url}")
                    prod['gre_url'] = page.url
                    prod['match_method'] = "Dynamic Search (Title Redirect)"
                    continue

                # Cerca link nella lista risultati
                found_url = await page.evaluate('''() => {
                    // Selettori comuni Gre per i link prodotto nella ricerca
                    const links = Array.from(document.querySelectorAll('.product-item a, a.product-name, .product-list a, .product-info h2 a'));
                    return links.length > 0 ? links[0].href : null;
                }''')

                if found_url:
                    print(f"   ✅ Trovato (List): {found_url}")
                    prod['gre_url'] = found_url
                    prod['match_method'] = "Dynamic Search (Title Result List)"
                else:
                    # Ultimo tentativo con SKU se presente
                    if prod['sku']:
                         print(f"   Refining search with SKU: {prod['sku']}")
                         await page.goto(f"https://www.grepool.com/it/ricerca?q={prod['sku']}", wait_until="load")
                         await page.wait_for_timeout(3000)
                         found_url = await page.evaluate('''() => {
                            const links = Array.from(document.querySelectorAll('.product-item a, a.product-name, .product-list a'));
                            return links.length > 0 ? links[0].href : null;
                         }''')
                         if found_url:
                             print(f"   ✅ Trovato (SKU List): {found_url}")
                             prod['gre_url'] = found_url
                             prod['match_method'] = "Dynamic Search (SKU Result List)"
                         else:
                             print(f"   ❌ Non trovato.")

            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_mapped_drafts_v5.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    
    found_count = len([p for p in products if p['gre_url']])
    print(f"\n✅ Mappatura V5 completata. Trovati: {found_count} / {len(products)}")

if __name__ == "__main__":
    asyncio.run(dynamic_mapping())
