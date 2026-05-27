import asyncio
from playwright.async_api import async_playwright
import sys
import os
import urllib.request

USER = "jollygam@libero.it"
PASS = "AntoRiky61"

async def fetch_ricambio(sku):
    os.makedirs("downloads/ricambi_images", exist_ok=True)
    save_path = f"downloads/ricambi_images/{sku}.jpg"

    print(f"🚀 Avvio ricerca per ricambio: {sku}")
    
    async with async_playwright() as p:
        # Avviamo con headless=False in modo da superare eventuali blocchi o Captcha
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        print("🔑 Collegamento a Fluidra in corso...")
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        
        # Accettazione Cookie se presente
        try:
            cookie_btn = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            await cookie_btn.wait_for(timeout=3000)
            if await cookie_btn.is_visible():
                await cookie_btn.click()
        except:
            pass

        # Compilazione Form di Login
        try:
            # Attendiamo che il campo appaia. Usiamo i selettori verificati.
            await page.wait_for_selector("input[name='login[username]'], input#email", timeout=10000)
            
            email_input = page.locator("input[name='login[username]'], input#email").first
            pass_input = page.locator("input[name='login[password]'], input#pass").first
            
            await email_input.fill(USER)
            await pass_input.fill(PASS)
            
            # Click sul bottone di login
            await page.locator("button.login, button[type='submit']").first.click()
            print("⏳ Login inviato. Attesa della dashboard (risolvi eventuali captcha se richiesti nella finestra)...")
            
            # Aspettiamo di atterrare sulla dashboard
            await page.wait_for_url("**/customer/account/**", timeout=45000)
            print("✅ Login riuscito!")
            
        except Exception as e:
            print("⚠️ Il login automatico ha impiegato troppo tempo o ha incontrato un blocco.")
            print("👉 Controlla la finestra del browser e completa il login manualmente se necessario.")
            # Aspettiamo che l'utente faccia login a mano
            try:
                await page.wait_for_url("**/customer/account/**", timeout=60000)
                print("✅ Login manuale rilevato!")
            except:
                print("❌ Tempo scaduto per il login. Chiusura.")
                await browser.close()
                return

        # Una volta loggati, cerchiamo lo SKU
        search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={sku}"
        print(f"🔎 Cerco lo SKU: {sku} sul sito...")
        await page.goto(search_url)
        await asyncio.sleep(4)
        
        print("📸 Ricerca dell'immagine nella pagina...")
        image_url = None
        try:
            # Attendiamo che la galleria fotorama venga caricata
            img_element = page.locator("img.fotorama__img, .fotorama__stage__frame img, img[src*='dam.fluidra.com']").first
            await img_element.wait_for(timeout=10000)
            image_url = await img_element.get_attribute("src")
        except:
            pass

        if image_url and "placeholder" not in image_url:
            print(f"✅ Immagine trovata: {image_url}")
            print(f"⬇️ Download in corso in {save_path}...")
            urllib.request.urlretrieve(image_url, save_path)
            print(f"🎉 Immagine scaricata con successo in: {save_path}")
            print("👉 Ora puoi caricarla nel Metaobject corrispondente su Shopify!")
        else:
            print(f"❌ Fluidra non ha un'immagine associata per lo SKU {sku}.")
            print("L'immagine non è disponibile nel loro catalogo B2B online.")

        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fetch_ricambio.py <SKU>")
        print("Esempio: python fetch_ricambio.py R0516700")
        sys.exit(1)
        
    sku_target = sys.argv[1]
    asyncio.run(fetch_ricambio(sku_target))
