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
    with open('master_sync_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    unique_skus = set()
    for p in data:
        if p['db'] == 'Fluidra':
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

        print("🔑 Login...")
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        try:
            await page.fill("input#email", USER)
            await page.fill("input#pass", PASS)
            await page.click("button.login")
            await page.wait_for_url("**/customer/account/**", timeout=20000)
        except:
            print("⚠️ Login manuale richiesto...")
            await page.wait_for_url("**/customer/account/**", timeout=60000)

        found_images = {}
        skus_to_process = list(unique_skus)
        
        for sku in skus_to_process:
            print(f"🔎 Cerco {sku}...")
            try:
                search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={sku}"
                await page.goto(search_url)
                await asyncio.sleep(3)
                
                # Se ci sono risultati, clicca sul primo
                first_result = page.locator(".product-item-link").first
                if await first_result.count() > 0:
                    await first_result.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(3)

                # Ora siamo (si spera) nella pagina prodotto, cerchiamo fotorama
                # L'immagine potrebbe essere in un href o in un tag img
                img_url = None
                
                # Prova 1: Selettore fotorama attivo
                img_element = page.locator(".fotorama__active img.fotorama__img").first
                if await img_element.count() > 0:
                    img_url = await img_element.get_attribute("src")
                
                # Prova 2: Qualunque immagine dam.fluidra.com
                if not img_url:
                    img_element = page.locator("img[src*='dam.fluidra.com']").first
                    if await img_element.count() > 0:
                        img_url = await img_element.get_attribute("src")

                if img_url and "placeholder" not in img_url:
                    found_images[sku] = img_url
                    print(f"  ✅ Trovata: {img_url}")
                    filename = f"{sku}.jpg"
                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                    urllib.request.urlretrieve(img_url, filepath)
                else:
                    print(f"  ❌ No image on product page")
            except Exception as e:
                print(f"  ⚠️ Errore per {sku}: {e}")

        await browser.close()

    with open('spare_parts_images_found.json', 'w', encoding='utf-8') as f:
        json.dump(found_images, f, indent=2)

if __name__ == "__main__":
    asyncio.run(bulk_fetch_ricambi_images())
