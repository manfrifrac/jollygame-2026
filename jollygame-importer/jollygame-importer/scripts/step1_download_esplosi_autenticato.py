import asyncio
from playwright.async_api import async_playwright
import json
import os
import urllib.request
import sqlite3
from dotenv import load_dotenv

load_dotenv()

USER = "jollygam@libero.it"
PASS = "AntoRiky61"
DB_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\fluidra_clean.db'
DOWNLOAD_DIR = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\downloads\esplosi'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def download_all_esplosi():
    # Carichiamo i match che avevamo già identificato (risparmiamo tempo query shopify)
    with open('esplosi_matches.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)

    print(f"🚀 Avvio download autenticato di {len(matches)} esplosi...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🔑 Login su Fluidra...")
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        
        try:
            # Gestione cookie
            cookie_btn = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            await cookie_btn.wait_for(timeout=5000)
            if await cookie_btn.is_visible():
                await cookie_btn.click()
        except: pass

        # Login manuale o auto
        try:
            await page.wait_for_selector("input#email", timeout=10000)
            await page.fill("input#email", USER)
            await page.fill("input#pass", PASS)
            await page.click("button.login")
            await page.wait_for_url("**/customer/account/**", timeout=30000)
            print("✅ Login riuscito!")
        except:
            print("⚠️ Login automatico fallito. Per favore completa il login a mano nella finestra...")
            await page.wait_for_url("**/customer/account/**", timeout=60000)
            print("✅ Login rilevato!")

        for match in matches:
            url = match['diagram_url']
            sku = match['sku']
            filename = f"{sku}_esploso.jpg"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            print(f"⬇️ Download {sku}...")
            try:
                # Usiamo page.evaluate per scaricare il file come blob e convertirlo in base64
                # o più semplicemente usiamo context.request per fare una get con i cookie
                response = await context.request.get(url)
                if response.status == 200:
                    body = await response.body()
                    with open(filepath, 'wb') as f:
                        f.write(body)
                    match['local_file'] = filepath
                    print(f"  ✅ Salvato: {filepath} ({len(body)} bytes)")
                else:
                    print(f"  ❌ Errore HTTP {response.status} per {url}")
            except Exception as e:
                print(f"  ❌ Fallito download {url}: {e}")

        await browser.close()

    # Aggiorniamo il file matches con i percorsi locali reali (quelli pesanti stavolta)
    with open('esplosi_matches.json', 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2)

if __name__ == "__main__":
    asyncio.run(download_all_esplosi())
