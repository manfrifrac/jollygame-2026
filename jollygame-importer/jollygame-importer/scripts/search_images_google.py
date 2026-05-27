import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def find_images_via_google():
    dump_path = "master_catalog_dump.json"
    if not os.path.exists(dump_path):
        print(f"File {dump_path} non trovato.")
        return

    with open(dump_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Solo prodotti con mediaCount 0 e SKU Gre
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Ricerca immagini per {len(missing)} prodotti via Google Images...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_images = []

        for prod in missing[:15]: # Small batch to test
            sku = prod['variants']['nodes'][0]['sku']
            query = f"Gre pool {sku} {prod['title'].split('.')[0]}"
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
            print(f"🔎 SKU {sku} -> {search_url}")
            
            try:
                await page.goto(search_url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(3000)

                # Gestione consenso Google
                if "consent.google" in page.url:
                    btn = page.locator("button:has-text('Accetto tutto'), button:has-text('Accept all')").first
                    if await btn.count() > 0:
                        await btn.click()
                        await page.wait_for_timeout(2000)

                # Estrazione immagini (Google Images structure)
                images = await page.evaluate('''() => {
                    const imgs = Array.from(document.querySelectorAll('img.rg_i, img.mNo69b, img.Q4LuWd'));
                    return imgs.map(img => img.src || img.dataset.src).filter(src => src && src.startsWith('http'));
                }''')

                # Filter out small thumbs or data urls
                valid_images = [img for img in images if not img.startswith('data:')][:3]

                if valid_images:
                    print(f"   ✅ Trovate {len(valid_images)} immagini.")
                    found_images.append({
                        "id": prod['id'],
                        "sku": sku,
                        "title": prod['title'],
                        "image_urls": valid_images
                    })
                else:
                    print(f"   ❌ Nessuna immagine valida trovata.")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("found_images_google.json", "w", encoding="utf-8") as f:
        json.dump(found_images, f, indent=2)

if __name__ == "__main__":
    asyncio.run(find_images_via_google())
