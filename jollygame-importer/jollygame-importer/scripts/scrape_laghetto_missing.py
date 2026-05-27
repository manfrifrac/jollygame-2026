import json
import asyncio
from playwright.async_api import async_playwright
import os
import requests
import re

async def scrape_laghetto_missing():
    # Carico i target (ho aggiornato get_missing_targets per includere vendor Laghetto)
    targets_path = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\jollygame-importer\jollygame-importer\missing_images_targets.json"
    if not os.path.exists(targets_path): return

    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    # Filtro solo i Laghetto
    laghetto_targets = [t for t in targets if "laghetto" in t['url'].lower()]
    
    print(f"🚀 Avvio Scraping Laghetto per {len(laghetto_targets)} prodotti...")
    output_dir = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\laghetto_images"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for target in laghetto_targets:
            title = target['title']
            url = target['url']
            print(f"\n🌊 Analisi Laghetto: {title}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2)
                
                # Selettori specifici per il sito Laghetto (WordPress + Elementor/Gallery)
                img_urls = await page.evaluate("""() => {
                    const images = Array.from(document.querySelectorAll('img'));
                    return images
                        .map(img => img.src || img.dataset.src)
                        .filter(src => src && src.includes('/wp-content/uploads/') && !src.includes('logo'))
                        .filter((v, i, a) => a.indexOf(v) === i);
                }""")

                if img_urls:
                    print(f"  📸 Trovate {len(img_urls)} immagini.")
                    safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
                    prod_dir = os.path.join(output_dir, safe_title)
                    os.makedirs(prod_dir, exist_ok=True)
                    
                    for i, img_url in enumerate(img_urls[:8]):
                        try:
                            # Pulizia URL dai parametri di ridimensionamento WordPress (es: -300x300.jpg)
                            clean_url = re.sub(r'-\d+x\d+\.(jpg|jpeg|png|webp)', r'.\1', img_url)
                            ext = clean_url.split(".")[-1].split("?")[0]
                            filename = f"{safe_title}_{i+1}.{ext}"
                            filepath = os.path.join(prod_dir, filename)
                            
                            res = requests.get(clean_url, timeout=15)
                            if res.status_code == 200:
                                with open(filepath, "wb") as f_img:
                                    f_img.write(res.content)
                                print(f"    ✅ Salvata: {filename}")
                        except: pass
                else:
                    print("  ⚠️ Nessuna immagine trovata.")
            except Exception as e:
                print(f"  ❌ Errore: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_laghetto_missing())
