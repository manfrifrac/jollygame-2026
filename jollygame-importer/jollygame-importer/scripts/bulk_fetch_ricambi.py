import asyncio
from playwright.async_api import async_playwright
import json
import os
import urllib.request
from dotenv import load_dotenv

load_dotenv()

USER = "jollygam@libero.it"
PASS = "AntoRiky61"
DOWNLOAD_DIR = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\downloads\ricambi_bulk'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def bulk_fetch_ricambi_images():
    # 1. Identifichiamo gli SKU senza immagine
    with open('master_sync_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    unique_skus = set()
    for p in data:
        if p['db'] == 'Fluidra': # Solo Fluidra ha il problema delle immagini mancanti nel DB
            for r in p['ricambi']:
                if not r['images'] or r['images'] == '[]':
                    unique_skus.add(r['sku'])

    print(f"🚀 Inizio ricerca online per {len(unique_skus)} ricambi Fluidra...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🔑 Login su Fluidra...")
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        try:
            await page.wait_for_selector("input#email", timeout=10000)
            await page.fill("input#email", USER)
            await page.fill("input#pass", PASS)
            await page.click("button.login")
            await page.wait_for_url("**/customer/account/**", timeout=20000)
            print("✅ Login riuscito!")
        except:
            print("⚠️ Login manuale richiesto...")
            await page.wait_for_url("**/customer/account/**", timeout=60000)

        # Mappa per salvare i nuovi URL trovati
        found_images = {}
        
        # Limitiamo a 30 per test o processiamo tutti?
        # L'utente vuole che lo faccia io, quindi provo a processarne un buon numero.
        skus_to_process = list(unique_skus)
        
        for sku in skus_to_process:
            print(f"🔎 Cerco {sku}...")
            try:
                search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={sku}"
                await page.goto(search_url)
                await asyncio.sleep(2)
                
                # Check for image
                img_element = page.locator("img.fotorama__img, .gallery-placeholder img, .product-image-photo").first
                if await img_element.count() > 0:
                    src = await img_element.get_attribute("src")
                    if src and "placeholder" not in src:
                        found_images[sku] = src
                        print(f"  ✅ Trovata: {src}")
                        
                        # Download immediato
                        filename = f"{sku}.jpg"
                        filepath = os.path.join(DOWNLOAD_DIR, filename)
                        urllib.request.urlretrieve(src, filepath)
                else:
                    print(f"  ❌ No image")
            except Exception as e:
                print(f"  ⚠️ Errore per {sku}: {e}")

        await browser.close()

    # Salva i risultati
    with open('spare_parts_images_found.json', 'w', encoding='utf-8') as f:
        json.dump(found_images, f, indent=2)
    print(f"\n🎉 Ricerca completata. Trovate {len(found_images)} immagini.")

if __name__ == "__main__":
    asyncio.run(bulk_fetch_ricambi_images())
