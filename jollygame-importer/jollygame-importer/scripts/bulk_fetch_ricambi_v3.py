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

    # skus_to_process = list(unique_skus)
    # Per test e velocità, iniziamo con una campionatura o quelli prioritari
    # Se vuoi farli tutti, basta togliere lo slice
    skus_to_process = list(unique_skus)

    print(f"🚀 Inizio ricerca online v3 per {len(skus_to_process)} ricambi Fluidra...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Visibile per debug/captcha
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
            print("✅ Login riuscito!")
        except:
            print("⚠️ Login manuale richiesto o già loggato...")
            try:
                await page.wait_for_url("**/customer/account/**", timeout=60000)
            except:
                pass

        found_images = {}
        
        for sku in skus_to_process:
            print(f"🔎 Cerco {sku}...")
            try:
                search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={sku}"
                await page.goto(search_url)
                
                # Aspettiamo che carichi o il primo risultato o la pagina prodotto (redirect)
                # Se atterriamo direttamente su .html è una pagina prodotto
                await asyncio.sleep(4)
                
                # Se siamo in una lista di ricerca, clicchiamo sul primo link
                results = page.locator(".product-item-link")
                if await results.count() > 0:
                    print(f"  - Lista risultati trovata, clicco sul primo...")
                    await results.first.click()
                    await asyncio.sleep(4)

                # Ora cerchiamo l'immagine con selettori multipli
                img_url = None
                
                # Selettore 1: Fotorama active image (quello che hai postato tu)
                selectors = [
                    ".fotorama__stage__frame.fotorama__active img.fotorama__img",
                    ".fotorama__stage__frame img",
                    "img.product-image-photo",
                    "img[src*='dam.fluidra.com']"
                ]
                
                for sel in selectors:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        src = await el.get_attribute("src")
                        if src and "placeholder" not in src:
                            img_url = src
                            break
                
                if img_url:
                    found_images[sku] = img_url
                    print(f"  ✅ Trovata: {img_url}")
                    
                    filename = f"{sku}.jpg"
                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                    # Usiamo il browser context per scaricare (così usiamo i cookie)
                    try:
                        response = await context.request.get(img_url)
                        if response.status == 200:
                            body = await response.body()
                            with open(filepath, 'wb') as f:
                                f.write(body)
                    except:
                        # Fallback se context.request fallisce
                        urllib.request.urlretrieve(img_url, filepath)
                else:
                    print(f"  ❌ Nessuna immagine trovata su {page.url}")
                    
            except Exception as e:
                print(f"  ⚠️ Errore per {sku}: {e}")

        await browser.close()

    # Aggiorna il file dei risultati
    current_found = {}
    if os.path.exists('spare_parts_images_found.json'):
        with open('spare_parts_images_found.json', 'r', encoding='utf-8') as f:
            current_found = json.load(f)
    
    current_found.update(found_images)
    
    with open('spare_parts_images_found.json', 'w', encoding='utf-8') as f:
        json.dump(current_found, f, indent=2)
    
    print(f"\n🎉 Fine sessione. Immagini trovate in totale: {len(current_found)}")

if __name__ == "__main__":
    asyncio.run(bulk_fetch_ricambi_images())
