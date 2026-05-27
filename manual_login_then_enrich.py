import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import sqlite3
import json
import re
from bs4 import BeautifulSoup
from rotate_vpn import rotate_mullvad

async def run_guided_enrich():
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM products WHERE is_spare_part=0 AND (ean IS NULL OR ean='N/A')")
    todo_urls = [r[0] for r in cursor.fetchall()]
    
    print(f"🚀 AVVIO GUIDATO: {len(todo_urls)} prodotti da fare.")

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_session_vpn")
        
        browser = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print("\n--- AZIONE RICHIESTA ---")
        print("1. Vai sulla pagina di login (se non ci sei già).")
        print("2. Effettua il login manualmente.")
        print("3. Una volta entrato nella dashboard, lo script partirà da solo tra 30 secondi.")
        
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        
        # Aspettiamo il login rilevando l'URL della dashboard o un timeout lungo
        try:
            await page.wait_for_url("**/customer/account/", timeout=120000)
            print("✅ Login rilevato! Inizio arricchimento tra 10 secondi...")
            await asyncio.sleep(10)
        except:
            print("⚠️ Timeout login, ma provo a procedere comunque...")

        semaphore = asyncio.Semaphore(3)
        async def worker(url):
            async with semaphore:
                p_new = await browser.new_page()
                try:
                    await p_new.goto(url, wait_until="load", timeout=60000)
                    await asyncio.sleep(8)
                    content = await p_new.content()
                    ean_match = re.search(r'EAN:?(\d{13})', content.replace(" ", ""), re.IGNORECASE)
                    ean = ean_match.group(1) if ean_match else "N/A"
                    
                    soup = BeautifulSoup(content, 'lxml')
                    h1 = soup.select_one("h1.page-title, h1")
                    title = h1.get_text(strip=True).split("|")[1].strip() if h1 and "|" in h1.get_text() else (h1.get_text(strip=True) if h1 else "N/A")

                    c = conn.cursor()
                    c.execute("UPDATE products SET ean=?, title=?, last_updated=CURRENT_TIMESTAMP WHERE url=?", (ean, title, url))
                    conn.commit()
                    print(f"   ✅ {ean} | {title[:30]}")
                except: pass
                finally: await p_new.close()

        # Esecuzione
        for i in range(0, len(todo_urls), 30):
            batch = todo_urls[i:i+30]
            await asyncio.gather(*[worker(u) for u in batch])
            # Piccola pausa tra blocchi
            await asyncio.sleep(5)

        await browser.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(run_guided_enrich())
