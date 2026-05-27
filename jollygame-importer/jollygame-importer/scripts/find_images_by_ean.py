import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def find_images_by_ean():
    # Carica Mappa EAN
    if not os.path.exists("sku_to_ean_map.json"):
        print("Mappa EAN non trovata.")
        return
    with open("sku_to_ean_map.json", "r", encoding="utf-8") as f:
        ean_map = json.load(f)

    # Carica Dump Shopify
    if not os.path.exists("master_catalog_dump.json"):
        print("Master dump non trovato.")
        return
    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Prodotti Gre senza foto
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre']
    print(f"🔍 Ricerca immagini per {len(missing)} prodotti via EAN...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_assets = []

        for prod in missing[:40]: # Batch 40
            sku = prod['variants']['nodes'][0].get('sku', '').strip().upper()
            ean = ean_map.get(sku)
            
            if not ean:
                print(f"⚠️  Nessun EAN per SKU {sku}, salto.")
                continue

            print(f"\n🔎 Cerco via EAN {ean} (Prodotto: {prod['title'][:40]}...)")
            
            try:
                # Query basata su EAN (il dato più preciso possibile)
                query = f"{ean} Gre pool"
                await page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", wait_until="load", timeout=30000)
                await page.wait_for_timeout(2000)
                
                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass
                    await page.wait_for_timeout(2000)

                # Trova link a rivenditori affidabili
                links = await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll('a'));
                    return anchors
                        .map(a => a.href)
                        .filter(h => h.includes('grepool.com') || h.includes('sanmarcopiscine') || h.includes('manomano') || h.includes('poolaria') || h.includes('piscinayspa') || h.includes('leroymerlin') || h.includes('amazon'));
                }''')
                
                if links:
                    target_url = links[0]
                    print(f"   ✅ Trovato link: {target_url}")
                    await page.goto(target_url, wait_until="load", timeout=20000)
                    await page.wait_for_timeout(3000)
                    
                    # Estrazione immagini
                    images = await page.evaluate('''() => {
                        const imgs = Array.from(document.querySelectorAll('.product-image-main img, .main-image img, #main-image, [itemprop="image"], .gallery__image, .product-images img, img[src*="catalog/product"], .pdp-main-image img'));
                        return [...new Set(imgs.map(img => img.src).filter(src => src && src.startsWith('http') && !src.includes('logo') && !src.includes('icon')))];
                    }''')
                    
                    if images:
                        print(f"   ✨ Trovate {len(images)} immagini.")
                        found_assets.append({
                            "id": prod['id'],
                            "sku": sku,
                            "ean": ean,
                            "image_urls": images[:6]
                        })
                    else:
                        print("   ❌ Nessuna immagine nel link.")
                else:
                    print("   ❌ Nessun link trovato via EAN.")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_images_by_ean.json", "w", encoding="utf-8") as f:
        json.dump(found_assets, f, indent=2)
    print(f"\n✅ Salvati dati per {len(found_assets)} prodotti.")

if __name__ == "__main__":
    asyncio.run(find_images_by_ean())
