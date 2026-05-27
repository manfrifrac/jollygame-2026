import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
import re

async def scrape_missing_data():
    dump_path = "master_catalog_dump.json"
    if not os.path.exists(dump_path):
        print(f"File {dump_path} non trovato.")
        return

    with open(dump_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Solo prodotti con mediaCount 0 e SKU Gre
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Ricerca dati per {len(missing)} prodotti su Grepool...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        enriched_data = []

        for prod in missing[:40]: # Batch di 40
            sku = prod['variants']['nodes'][0]['sku']
            # Rimuoviamo suffix N o GY per la ricerca se necessario
            search_sku = re.sub(r'[NGY]+$', '', sku)
            search_url = f"https://www.grepool.com/it/ricerca?q={search_sku}"
            print(f"🔎 SKU {sku} (Ricerca: {search_sku})")
            
            try:
                await page.goto(search_url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(2000)

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

                # Estrazione Specifiche
                specs = await page.evaluate('''() => {
                    const data = {};
                    document.querySelectorAll('.product-info-main .attribute, table tr').forEach(el => {
                        const labelEl = el.querySelector('.label, th');
                        const valueEl = el.querySelector('.value, td');
                        if (labelEl && valueEl) {
                            data[labelEl.innerText.trim()] = valueEl.innerText.trim();
                        }
                    });
                    return data;
                }''')

                if images:
                    print(f"   ✅ Trovate {len(images)} immagini e {len(specs)} specifiche.")
                    enriched_data.append({
                        "id": prod['id'],
                        "sku": sku,
                        "image_urls": images[:6],
                        "specs": specs
                    })
                else:
                    print(f"   ❌ Nulla trovato.")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_enriched_assets.json", "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(scrape_missing_data())
