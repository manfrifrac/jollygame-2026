import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def generate_preview():
    # 1. Carica Mappa EAN
    if not os.path.exists("sku_to_ean_map.json"):
        print("Mappa EAN non trovata.")
        return
    with open("sku_to_ean_map.json", "r", encoding="utf-8") as f:
        ean_map = json.load(f)

    # 2. Carica Master Dump
    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre' and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Avvio generazione anteprime per {len(missing)} prodotti...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        preview_data = []

        for prod in missing[:15]: # Prendiamo i primi 15 per un controllo veloce
            sku = prod['variants']['nodes'][0]['sku'].strip().upper()
            ean = ean_map.get(sku)
            if not ean: continue

            print(f"🔎 Cerco: {prod['title'][:30]}... (EAN {ean})")
            
            try:
                # Cerca su Google per trovare il sito più ricco di foto
                query = f"{ean} Gre pool"
                await page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", wait_until="load")
                await page.wait_for_timeout(2000)

                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass

                links = await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll('a'));
                    return anchors
                        .map(a => a.href)
                        .filter(h => h.includes('grepool.com') || h.includes('sanmarcopiscine') || h.includes('manomano') || h.includes('eprice'));
                }''')

                if links:
                    target_url = links[0]
                    await page.goto(target_url, wait_until="load", timeout=20000)
                    await page.wait_for_timeout(2000)
                    
                    images = await page.evaluate('''() => {
                        const imgs = Array.from(document.querySelectorAll('.product-image-main img, .main-image img, #main-image, [itemprop="image"], .gallery__image, .product-images img, .pdp-main-image img'));
                        return [...new Set(imgs.map(img => img.src).filter(src => src && src.startsWith('http') && !src.includes('logo')))];
                    }''')
                    
                    if images:
                        preview_data.append({
                            "title": prod['title'],
                            "sku": sku,
                            "ean": ean,
                            "source_url": target_url,
                            "image_previews": images[:3] # Mostra 3 link
                        })
                        print(f"   ✅ Trovate {len(images)} foto.")
                    else:
                        print("   ❌ Nessuna foto nel link.")
                else:
                    print("   ❌ Nessun link trovato.")

            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_image_preview_report.json", "w", encoding="utf-8") as f:
        json.dump(preview_data, f, indent=2)
    
    print("\n✅ Report anteprime salvato in 'gre_image_preview_report.json'")
    print("📋 Puoi visualizzarlo ora per confermare i link.")

if __name__ == "__main__":
    asyncio.run(generate_preview())
