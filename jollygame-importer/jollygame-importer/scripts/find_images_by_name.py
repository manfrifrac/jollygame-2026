import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os

async def find_images_by_common_name():
    with open("master_catalog_dump.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Solo prodotti Gre senza foto
    missing = [p for p in catalog if p['mediaCount']['count'] == 0 and p.get('vendor') == 'Gre']
    print(f"🔍 Ricerca per nome commerciale per {len(missing)} prodotti...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        preview_data = []

        # Proviamo a dedurre i nomi commerciali dai titoli lunghi
        # Esempio: "KIT Piscina ovale decorazione nordic con sistema omega... 730x375" -> "Piscina Gre Islanda 730x375"
        for prod in missing[:10]:
            title = prod['title']
            sku = prod['variants']['nodes'][0]['sku']
            
            # Logica di "pulizia" nome commerciale
            common_name = "Piscina Gre"
            if "nordic" in title.lower(): common_name += " Islanda"
            elif "grigio antracite" in title.lower(): common_name += " Island"
            elif "bianca" in title.lower(): common_name += " Haiti"
            elif "legno" in title.lower() and "sistema omega" in title.lower(): common_name += " Amazonia"
            
            # Aggiungi dimensioni
            dim_match = title.split("Dim:")
            if len(dim_match) > 1:
                common_name += " " + dim_match[1].split()[0]
            
            print(f"🔎 Cerco: {common_name} (SKU {sku})")
            
            try:
                # Cerca su Google Images
                search_url = f"https://www.google.com/search?q={common_name.replace(' ', '+')}&tbm=isch"
                await page.goto(search_url, wait_until="load")
                await page.wait_for_timeout(3000)

                if "consent.google" in page.url:
                    try: await page.locator("button:has-text('Accetto tutto')").first.click()
                    except: pass
                    await page.wait_for_timeout(2000)

                images = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('img'))
                        .map(img => img.src || img.dataset.src || img.dataset.iurl)
                        .filter(src => src && src.startsWith('http') && !src.includes('gstatic.com'))
                        .slice(0, 3);
                }''')
                
                if images:
                    preview_data.append({
                        "title": title,
                        "common_name": common_name,
                        "sku": sku,
                        "image_links": images
                    })
                    print(f"   ✅ Trovate {len(images)} foto.")
                else:
                    print("   ❌ Nessuna foto trovata.")

            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser.close()

    with open("gre_common_name_preview.json", "w", encoding="utf-8") as f:
        json.dump(preview_data, f, indent=2)
    
    print("\n✅ Report salvato in 'gre_common_name_preview.json'")

if __name__ == "__main__":
    asyncio.run(find_images_by_common_name())
