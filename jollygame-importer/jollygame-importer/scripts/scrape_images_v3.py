import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
import re

async def scrape_images_v3():
    dump_path = "master_catalog_dump.json"
    if not os.path.exists(dump_path):
        print(f"File {dump_path} non trovato.")
        return

    with open(dump_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Focus on the most expensive new products (Pools)
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and "Listino:2026" in (p.get('tags', []))]
    
    # Sort by price descending if possible, but price is not in dump
    # Let's just take products starting with "KIT Piscina"
    pools = [p for p in missing if "KIT Piscina" in p['title']]
    print(f"🔍 Ricerca immagini per {len(pools)} nuove piscine via Google...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        found_assets = []

        for prod in pools[:30]: # Process 30 pools
            sku = prod['variants']['nodes'][0]['sku']
            title = prod['title']
            
            # Clean title for better search
            # "KIT Piscina ovale decorazione nordic con sistema omega... Dim: 730x375 h 132"
            search_query = title.split("Include")[0].split("Dim:")[0].strip()
            if sku: search_query += f" {sku}"
            
            print(f"\n🔎 Cerco: {search_query}")
            
            try:
                # Search on Google Images directly
                await page.goto(f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch", wait_until="load")
                await page.wait_for_timeout(4000)

                # Consent
                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass
                    await page.wait_for_timeout(2000)

                # Extract images
                images = await page.evaluate('''() => {
                    const imgs = Array.from(document.querySelectorAll('img.rg_i, img.mNo69b, img.Q4LuWd'));
                    return imgs.map(img => img.src || img.dataset.src).filter(src => src && src.startsWith('http') && !src.includes('gstatic.com'));
                }''')

                if images:
                    print(f"   ✅ Trovate {len(images)} immagini.")
                    found_assets.append({
                        "id": prod['id'],
                        "sku": sku,
                        "title": prod['title'],
                        "image_urls": images[:3]
                    })
                else:
                    # Backup: try generic search and look for big images in results
                    print(f"   ⚠️ Nessuna immagine diretta. Provo ricerca web...")
                    await page.goto(f"https://www.google.com/search?q={search_query.replace(' ', '+')}", wait_until="load")
                    await page.wait_for_timeout(3000)
                    
                    # Look for images in the page
                    web_images = await page.evaluate('''() => {
                        const imgs = Array.from(document.querySelectorAll('img'));
                        return imgs.map(img => img.src).filter(src => src && src.startsWith('http') && src.includes('product') && !src.includes('icon'));
                    }''')
                    if web_images:
                         print(f"   ✅ Trovate {len(web_images)} immagini web.")
                         found_assets.append({
                            "id": prod['id'],
                            "sku": sku,
                            "title": prod['title'],
                            "image_urls": web_images[:3]
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
    asyncio.run(scrape_images_v3())
