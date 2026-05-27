import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
import re

async def scrape_images_v2():
    dump_path = "master_catalog_dump.json"
    if not os.path.exists(dump_path):
        print(f"File {dump_path} non trovato.")
        return

    with open(dump_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Solo prodotti senza foto e con tag Listino:2026
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and "Listino:2026" in (p.get('tags', []))]
    print(f"🔍 Ricerca immagini per {len(missing)} nuovi prodotti via Grepool...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_assets = []

        for prod in missing[:50]: # Batch di 50
            sku = prod['variants']['nodes'][0]['sku']
            title = prod['title']
            
            # Strategia 1: Cerca per SKU (pulito)
            search_query = re.sub(r'[NGY]+$', '', sku) if sku else title
            print(f"\n🔎 Cerco: {search_query}")
            
            try:
                await page.goto(f"https://www.grepool.com/it/ricerca?q={search_query.replace(' ', '+')}", wait_until="load", timeout=30000)
                await page.wait_for_timeout(2000)

                # Se non trova nulla con SKU, prova con Titolo parziale
                if await page.locator(".no-results").count() > 0 or "ricerca" in page.url:
                    # Estrai una parte significativa del titolo (es. prima di "Dim:")
                    short_title = title.split("Dim:")[0].split(".")[0].replace("KIT Piscina", "").strip()
                    if len(short_title) > 10:
                        print(f"   Refining search with title: {short_title}")
                        await page.goto(f"https://www.grepool.com/it/ricerca?q={short_title.replace(' ', '+')}", wait_until="load")
                        await page.wait_for_timeout(2000)

                # Se siamo su pagina ricerca, clicca il primo prodotto
                if "ricerca" in page.url:
                    first_item = page.locator(".product-item-link, a.product-name").first
                    if await first_item.count() > 0:
                        await first_item.click()
                        await page.wait_for_timeout(3000)

                # Estrazione Immagini
                images = await page.evaluate('''() => {
                    const imgs = Array.from(document.querySelectorAll('.product-image-main img, .gallery-placeholder__image, .product-images img, .main-image img'));
                    return [...new Set(imgs.map(img => img.src).filter(src => src && src.startsWith('http')))];
                }''')

                if images:
                    print(f"   ✅ Trovate {len(images)} immagini.")
                    found_assets.append({
                        "id": prod['id'],
                        "sku": sku,
                        "image_urls": images[:5]
                    })
                else:
                    print(f"   ❌ Nulla trovato.")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_new_images_found.json", "w", encoding="utf-8") as f:
        json.dump(found_assets, f, indent=2)
    
    print(f"\n✅ Ricerca completata. Trovate immagini per {len(found_assets)} prodotti.")

if __name__ == "__main__":
    asyncio.run(scrape_images_v2())
