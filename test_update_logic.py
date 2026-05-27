import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import re
from bs4 import BeautifulSoup
import json

async def test_update_logic(urls):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)

        results = []
        for url in urls:
            print(f"\n🔍 TEST SU: {url}")
            try:
                await page.goto(url, wait_until="load", timeout=60000)
                await asyncio.sleep(8) # Attesa JS

                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # 1. TEST EAN (Regex Flessibile)
                ean = "N/A"
                ean_match = re.search(r'EAN:\s*(\d{8,13})', content, re.IGNORECASE)
                if ean_match:
                    ean = ean_match.group(1)
                
                # 2. TEST TITOLO (Gestione 404 e Pipe)
                title = "N/A"
                h1 = soup.select_one("h1.page-title, h1")
                if h1:
                    h1_text = h1.get_text(strip=True)
                    if "dispiace" in h1_text.lower() or "not found" in h1_text.lower():
                        title = "[PAGINA NON TROVATA]"
                    elif "|" in h1_text:
                        title = h1_text.split("|")[1].strip()
                    else:
                        title = h1_text
                
                # 3. TEST SPECIFICHE
                specs = len(soup.select("table.additional-attributes tr"))
                
                print(f"   ✅ RISULTATO: Title: {title} | EAN: {ean} | Specs: {specs}")
                results.append({"url": url, "title": title, "ean": ean, "specs": specs})
                
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        await browser_context.close()
    
    with open("audit_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    test_urls = [
        "https://pro.fluidra.com/it_it/1284501-cnx-50-iq.html",
        "https://pro.fluidra.com/it_it/640725-d20.html",
        "https://pro.fluidra.com/it_it/640256-1.html",
        "https://pro.fluidra.com/it_it/1005633-e-next-ph-30.html"
    ]
    asyncio.run(test_update_logic(test_urls))
