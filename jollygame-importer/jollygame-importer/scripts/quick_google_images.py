import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def quick_google_images():
    with open("sku_to_ean_map.json", "r", encoding="utf-8") as f:
        ean_map = json.load(f)
    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre' and p['variants']['nodes'][0].get('sku')]
    print(f"🔍 Ricerca 'veloce' su Google per {len(missing)} prodotti...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        preview_data = []

        for prod in missing[:5]: # Solo i primi 5 per testare la qualità
            sku = prod['variants']['nodes'][0]['sku'].strip().upper()
            ean = ean_map.get(sku)
            if not ean: continue

            print(f"🔎 Cerco EAN {ean}")
            
            try:
                # Usiamo Google Images con query pulitissima
                search_url = f"https://www.google.com/search?q={ean}+gre+piscina&tbm=isch"
                await page.goto(search_url, wait_until="load")
                await page.wait_for_timeout(3000)

                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass
                    await page.wait_for_timeout(2000)

                # Estrarre i primi 3 link immagine diretti (Google Images inietta immagini in modo complesso)
                # Proviamo a catturare gli src di img che hanno dimensioni decenti
                images = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('img'))
                        .map(img => img.src || img.dataset.src || img.dataset.iurl)
                        .filter(src => src && src.startsWith('http') && !src.includes('gstatic.com') && !src.includes('google.'))
                        .slice(0, 3);
                }''')
                
                if images:
                    preview_data.append({
                        "title": prod['title'],
                        "sku": sku,
                        "ean": ean,
                        "image_links": images
                    })
                    print(f"   ✅ Trovate {len(images)} foto.")
                else:
                    print("   ❌ Nessuna foto trovata.")

            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_quick_preview.json", "w", encoding="utf-8") as f:
        json.dump(preview_data, f, indent=2)
    
    print("\n✅ Anteprima rapida generata in 'gre_quick_preview.json'")

if __name__ == "__main__":
    asyncio.run(quick_google_images())
