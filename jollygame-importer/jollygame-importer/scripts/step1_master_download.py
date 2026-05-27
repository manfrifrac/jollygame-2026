import json
import os
import requests
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

USER = "jollygam@libero.it"
PASS = "AntoRiky61"
DOWNLOAD_DIR = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\downloads\master_sync'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def download_all_resources():
    with open('master_sync_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    urls_to_download = set()
    
    # Collect all diagram URLs
    for p in data:
        if p['diagram_url']:
            urls_to_download.add(p['diagram_url'])
        
        # Collect all spare part image URLs
        for r in p['ricambi']:
            if r['images'] and r['images'] != '[]' and r['images'] != '':
                try:
                    # In Fluidra it's a JSON array
                    if p['db'] == 'Fluidra':
                        imgs = json.loads(r['images'])
                        if imgs: urls_to_download.add(imgs[0])
                    else:
                        # Bestway/Intex might be comma separated or single
                        urls_to_download.add(r['images'].split(',')[0].strip())
                except:
                    pass

    print(f"🚀 Trovati {len(urls_to_download)} file unici da scaricare.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🔑 Login su Fluidra (per sicurezza)...")
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        try:
            await page.wait_for_selector("input#email", timeout=5000)
            await page.fill("input#email", USER)
            await page.fill("input#pass", PASS)
            await page.click("button.login")
            await page.wait_for_url("**/customer/account/**", timeout=20000)
            print("✅ Login riuscito!")
        except:
            print("⚠️ Login non riuscito o già effettuato.")

        download_map = {}
        for url in urls_to_download:
            # Generate safe filename
            safe_name = "".join([c if c.isalnum() else "_" for c in url.split('/')[-1]])
            if not safe_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                safe_name += ".jpg"
            
            filepath = os.path.join(DOWNLOAD_DIR, safe_name)
            
            if os.path.exists(filepath):
                download_map[url] = filepath
                continue

            print(f"⬇️ Scarico: {url}...")
            try:
                # Use context.request to carry cookies
                response = await context.request.get(url)
                if response.status == 200:
                    body = await response.body()
                    with open(filepath, 'wb') as f:
                        f.write(body)
                    download_map[url] = filepath
                    print(f"  ✅ Salvato: {safe_name}")
                else:
                    print(f"  ❌ Errore HTTP {response.status}")
            except Exception as e:
                print(f"  ❌ Fallito: {e}")

        await browser.close()

    # Salviamo la mappa di download per lo step successivo
    with open('download_map.json', 'w', encoding='utf-8') as f:
        json.dump(download_map, f, indent=2)
    print("\n🎉 Download completato. Mappa salvata in download_map.json")

if __name__ == "__main__":
    asyncio.run(download_all_resources())
