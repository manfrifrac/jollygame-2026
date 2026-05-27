import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def find_images_by_ean():
    dump_path = "master_catalog_dump.json"
    if not os.path.exists(dump_path):
        print(f"File {dump_path} non trovato.")
        return
        
    with open(dump_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Solo prodotti Gre senza foto
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre']
    print(f"🔍 Analisi di {len(missing)} prodotti Gre senza foto...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_assets = []

        for prod in missing[:40]: # Batch 40
            sku = prod['variants']['nodes'][0].get('sku')
            title = prod['title']
            
            print(f"\n🔎 Cerco immagini per: {title} (SKU: {sku})")
            
            # Cerca su Google Web
            query = f"Gre {sku if sku else ''} {title.split('Dim:')[0]}"
            try:
                await page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", wait_until="load", timeout=30000)
                await page.wait_for_timeout(2000)
                
                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass
                    await page.wait_for_timeout(2000)

                # Cerca link a siti di piscine
                links = await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll('a'));
                    return anchors
                        .map(a => a.href)
                        .filter(h => h.includes('grepool.com') || h.includes('sanmarcopiscine') || h.includes('manomano') || h.includes('poolaria') || h.includes('piscinayspa') || h.includes('leroymerlin'));
                }''')
                
                if links:
                    target_url = links[0]
                    print(f"   ✅ Trovato link: {target_url}")
                    try:
                        await page.goto(target_url, wait_until="load", timeout=20000)
                        await page.wait_for_timeout(3000)
                        
                        # Estrai immagini
                        images = await page.evaluate('''() => {
                            const imgs = Array.from(document.querySelectorAll('.product-image-main img, .main-image img, #main-image, [itemprop="image"], .gallery__image, .product-images img, img[src*="catalog/product"]'));
                            return [...new Set(imgs.map(img => img.src).filter(src => src && src.startsWith('http') && !src.includes('logo') && !src.includes('icon') && !src.includes('badge')))];
                        }''')
                        
                        if images:
                            print(f"   ✨ Trovate {len(images)} immagini.")
                            found_assets.append({
                                "id": prod['id'],
                                "sku": sku,
                                "image_urls": images[:5]
                            })
                        else:
                            print("   ❌ Nessuna immagine trovata nel link.")
                    except:
                        print("   ❌ Errore caricamento link.")
                else:
                    print("   ❌ Nessun link utile trovato.")
            except Exception as e:
                print(f"   ❌ Errore Google: {e}")

        await browser.close()

    with open("gre_scraped_images.json", "w", encoding="utf-8") as f:
        json.dump(found_assets, f, indent=2)
    print(f"\n✅ Salvati dati per {len(found_assets)} prodotti.")

if __name__ == "__main__":
    asyncio.run(find_images_by_ean())
