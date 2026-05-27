import json
import asyncio
from playwright.async_api import async_playwright
import os
import requests
import re

async def scrape_missing_images():
    targets_path = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\jollygame-importer\jollygame-importer\missing_images_targets.json"
    if not os.path.exists(targets_path):
        print("Targets not found")
        return

    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"🚀 Avvio Deep Scraping per {len(targets)} prodotti...")
    output_dir = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\zodiac_images"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for target in targets:
            title = target['title']
            url = target['url']
            print(f"\n🔍 Analisi: {title} ({url})")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2) # Attesa extra per JS
                
                selectors = [
                    "img[src*='fluidra']", "img[src*='bynder']",
                    "img[src*='assets']", ".product-gallery img",
                    ".main-image img", "div[style*='background-image']"
                ]
                
                img_urls = []
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        src = await el.get_attribute("src") or await el.get_attribute("data-src") or await el.get_attribute("data-lazy")
                        if not src:
                            style = await el.get_attribute("style")
                            if style and "url(" in style:
                                src = style.split("url(")[1].split(")")[0].replace('"', '').replace("'", "")
                        
                        if src and "http" in src and src not in img_urls:
                            src = src.replace("/Medium/", "/Original/").replace("-Medium", "-Original")
                            img_urls.append(src)

                if img_urls:
                    print(f"  📸 Trovate {len(img_urls)} immagini.")
                    safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
                    prod_dir = os.path.join(output_dir, safe_title)
                    os.makedirs(prod_dir, exist_ok=True)
                    
                    for i, img_url in enumerate(img_urls[:5]):
                        try:
                            ext = img_url.split(".")[-1].split("?")[0]
                            if len(ext) > 4: ext = "jpg"
                            filename = f"{safe_title}_{i+1}.{ext}"
                            filepath = os.path.join(prod_dir, filename)
                            
                            res = requests.get(img_url, timeout=15)
                            if res.status_code == 200:
                                with open(filepath, "wb") as f_img:
                                    f_img.write(res.content)
                                print(f"    ✅ Salvata: {filename}")
                        except Exception as e:
                            print(f"    ❌ Errore download {img_url}: {e}")
                else:
                    print("  ⚠️ Nessuna immagine trovata.")

            except Exception as e:
                print(f"  ❌ Errore navigazione: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_missing_images())
