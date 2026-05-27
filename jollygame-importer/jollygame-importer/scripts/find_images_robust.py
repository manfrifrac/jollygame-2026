import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def find_images_final():
    with open("sku_to_ean_map.json", "r", encoding="utf-8") as f:
        ean_map = json.load(f)
    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre']
    print(f"🚀 Ricerca immagini via EAN (Metodo Robusto) per {len(missing)} prodotti...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_assets = []

        for prod in missing[:20]: # Batch di 20
            v = prod['variants']['nodes'][0]
            if not v: continue
            sku = (v.get('sku') or "").strip().upper()
            ean = ean_map.get(sku)
            
            if not ean: continue

            print(f"🔎 Analisi: {sku} (EAN {ean})")
            
            try:
                # 1. Ricerca Web per trovare la pagina prodotto
                query = f"{ean} Gre pool"
                await page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", wait_until="load")
                await page.wait_for_timeout(2000)
                
                # Chiudi consenso
                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass
                    await page.wait_for_timeout(1500)

                # Cerca link utili
                links = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => a.href)
                        .filter(h => h.includes('grepool.com') || h.includes('sanmarcopiscine') || h.includes('manomano') || h.includes('eprice') || h.includes('climaconvenienza') || h.includes('leroymerlin'));
                }''')
                
                if links:
                    target_url = links[0]
                    print(f"   ✅ Navigo su: {target_url}")
                    await page.goto(target_url, wait_until="load", timeout=20000)
                    await page.wait_for_timeout(2500)
                    
                    # Estrazione Immagini Principali
                    # Selettori avanzati per vari siti
                    img_selectors = [
                        '.product-image-main img', '.main-image img', '#main-image', 
                        '[itemprop="image"]', '.gallery__image', '.product-images img',
                        'img[src*="catalog/product"]', '.pdp-main-image img',
                        '.zoom-image img', '.main-product-img'
                    ]
                    
                    images = await page.evaluate('''(selectors) => {
                        const results = [];
                        selectors.forEach(s => {
                            document.querySelectorAll(s).forEach(img => {
                                if (img.src && img.src.startsWith('http') && !img.src.includes('logo') && !img.src.includes('icon')) {
                                    results.push(img.src.split('?')[0]);
                                }
                            });
                        });
                        return [...new Set(results)];
                    }''', img_selectors)
                    
                    if images:
                        print(f"   ✨ Trovate {len(images)} immagini.")
                        found_assets.append({
                            "id": prod['id'],
                            "sku": sku,
                            "image_urls": images[:5]
                        })
                    else:
                        print("   ❌ Nessuna immagine nel link.")
                else:
                    print("   ❌ Nessun link utile nei risultati.")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_final_images_found.json", "w", encoding="utf-8") as f:
        json.dump(found_assets, f, indent=2)

if __name__ == "__main__":
    asyncio.run(find_images_final())
