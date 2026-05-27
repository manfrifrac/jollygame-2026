import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def generate_preview_sanmarco():
    with open("sku_to_ean_map.json", "r", encoding="utf-8") as f:
        ean_map = json.load(f)
    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre' and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Ricerca su San Marco per {len(missing)} prodotti...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        preview_data = []

        for prod in missing[:10]: # Batch di 10
            sku = prod['variants']['nodes'][0]['sku'].strip().upper()
            ean = ean_map.get(sku)
            if not ean: continue

            print(f"🔎 SKU {sku} (EAN {ean})")
            
            try:
                # Ricerca diretta su San Marco via URL query
                search_url = f"https://www.grupposanmarco.eu/catalogsearch/result/?q={ean}"
                await page.goto(search_url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(3000)

                # Clicca il primo prodotto se siamo in lista
                first_item = page.locator(".product-item-link").first
                if await first_item.count() > 0:
                    await first_item.click()
                    await page.wait_for_timeout(3000)

                # Estrazione immagini
                images = await page.evaluate('''() => {
                    const results = [];
                    // San Marco usa spesso Fotorama o classi specifiche
                    document.querySelectorAll('img.fotorama__img, .product-image-main img, .gallery-placeholder__image').forEach(img => {
                        if (img.src && img.src.startsWith('http')) results.push(img.src);
                    });
                    return [...new Set(results)];
                }''')
                
                if images:
                    preview_data.append({
                        "title": prod['title'],
                        "sku": sku,
                        "ean": ean,
                        "source": "San Marco",
                        "image_previews": images[:3]
                    })
                    print(f"   ✅ Trovate {len(images)} foto.")
                else:
                    print("   ❌ Nessuna foto trovata.")

            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_image_preview_sanmarco.json", "w", encoding="utf-8") as f:
        json.dump(preview_data, f, indent=2)
    
    print("\n✅ Report salvato in 'gre_image_preview_sanmarco.json'")

if __name__ == "__main__":
    asyncio.run(generate_preview_sanmarco())
