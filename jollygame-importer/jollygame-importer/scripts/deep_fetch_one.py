import asyncio
from playwright.async_api import async_playwright
import os
import urllib.request

USER = "jollygam@libero.it"
PASS = "AntoRiky61"

async def fetch_one(sku):
    async with async_playwright() as p:
        # Usiamo un browser vero con profilo utente finto per evitare bot detection
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        print(f"🚀 Cerco di recuperare l'immagine per {sku}...")
        
        # 1. Login
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        try:
            await page.fill("input#email", USER)
            await page.fill("input#pass", PASS)
            await page.click("button.login")
            await page.wait_for_url("**/customer/account/**", timeout=20000)
            print("✅ Login OK")
        except:
            print("⚠️ Login automatico fallito. Per favore completa il login se necessario nella finestra...")
            await page.wait_for_url("**/customer/account/**", timeout=60000)

        # 2. Ricerca
        search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={sku}"
        await page.goto(search_url)
        await asyncio.sleep(5)
        
        # 3. Selettore specifico per il link del prodotto
        try:
            product_link = page.locator("a.product-item-link").first
            if await product_link.count() > 0:
                print("🔗 Clicco sul prodotto trovato...")
                await product_link.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(5)
        except: pass

        # 4. Estrazione immagine
        print("📸 Cerco l'immagine finale...")
        img_url = None
        
        # Selettori in ordine di priorità
        selectors = [
            ".fotorama__stage__frame.fotorama__active img.fotorama__img",
            "img.fotorama__img",
            ".gallery-placeholder img",
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
            print(f"🎯 URL Trovata: {img_url}")
            os.makedirs("downloads/ricambi_images", exist_ok=True)
            path = f"downloads/ricambi_images/{sku}.jpg"
            urllib.request.urlretrieve(img_url, path)
            print(f"✅ Immagine salvata in {path}")
        else:
            print("❌ Immagine non trovata. Salvataggio screenshot di debug...")
            await page.screenshot(path=f"debug_failed_{sku}.png")
            
        await browser.close()

if __name__ == "__main__":
    import sys
    sku = sys.argv[1] if len(sys.argv) > 1 else "R0516700"
    asyncio.run(fetch_one(sku))
