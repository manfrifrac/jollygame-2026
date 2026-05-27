import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def scrape_missing_images():
    if not os.path.exists("master_catalog_dump.json"):
        print("File master_catalog_dump.json non trovato.")
        return

    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Ricerca immagini per {len(missing)} prodotti via Grepool...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_images = []

        for prod in missing[:50]: # Process 50 products at a time
            sku = prod['variants']['nodes'][0]['sku']
            search_url = f"https://www.grepool.com/it/ricerca?q={sku}"
            print(f"🔎 SKU {sku} -> {search_url}")
            
            try:
                await page.goto(search_url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(3000)

                # Se siamo su pagina ricerca, cerca il primo prodotto
                if "ricerca" in page.url:
                    first_item = page.locator(".product-item-link, a.product-name").first
                    if await first_item.count() > 0:
                        await first_item.click()
                        await page.wait_for_timeout(3000)

                # Estrai immagini
                images = await page.evaluate('''() => {
                    const imgs = Array.from(document.querySelectorAll('.product-image-main img, .gallery-placeholder__image, .product-images img, .main-image img'));
                    return imgs.map(img => img.src).filter(src => src && src.startsWith('http'));
                }''')

                if images:
                    # Rimuovi duplicati e pulisci URL (rimuovi parametri query)
                    unique_images = []
                    seen = set()
                    for img in images:
                        clean_url = img.split('?')[0]
                        if clean_url not in seen:
                            seen.add(clean_url)
                            unique_images.append(clean_url)

                    print(f"   ✅ Trovate {len(unique_images)} immagini.")
                    found_images.append({
                        "id": prod['id'],
                        "sku": sku,
                        "title": prod['title'],
                        "image_urls": unique_images[:5]
                    })
                else:
                    print(f"   ❌ Nessuna immagine trovata.")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("found_images_gre.json", "w", encoding="utf-8") as f:
        json.dump(found_images, f, indent=2)
    
    print(f"\n✅ Ricerca completata. Salvati dati per {len(found_images)} prodotti.")

if __name__ == "__main__":
    asyncio.run(scrape_missing_images())
