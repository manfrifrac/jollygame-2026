import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
import json
import re
import sqlite3
from rotate_vpn import rotate_mullvad
from bs4 import BeautifulSoup

# CREDENZIALI FLUIDRA
USER = "jollygam@libero.it"
PASS = "AntoRiky61"

async def perform_login(page):
    """Esegue il login automatico sul Identity Provider di Fluidra."""
    print(f"🔑 Tentativo di login (Fluidra Auth0) per: {USER}")
    try:
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/", wait_until="load", timeout=90000)
        await asyncio.sleep(5)
        
        # Cookie
        try:
            cookie_btn = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            if await cookie_btn.is_visible():
                await cookie_btn.click()
                await asyncio.sleep(2)
        except: pass

        # Login Auth0
        await page.wait_for_selector("input#username", timeout=30000)
        await page.fill("input#username", USER)
        await page.fill("input#password", PASS)
        await asyncio.sleep(1)
        await page.click("button[type='submit']")
        
        # Attesa dashboard
        await page.wait_for_url("**/customer/account/", timeout=60000)
        print("✅ Login Fluidra completato!")
        return True
    except Exception as e:
        print(f"❌ Errore login Fluidra: {e}")
        return False

async def enrich_fluidra_turbo(concurrency=3, vpn_rotate_every=40):
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()
    # Cerchiamo prodotti principali Fluidra senza EAN
    cursor.execute("SELECT url FROM products WHERE is_spare_part=0 AND (ean IS NULL OR ean='N/A')")
    todo_urls = [r[0] for r in cursor.fetchall()]
    
    print(f"🚀 AVVIO ARRICCHIMENTO FLUIDRA (Prodotti rimanenti: {len(todo_urls)})")

    if not todo_urls:
        print("✅ Tutto completato!")
        return

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_session_vpn")
        
        async def launch_and_login():
            context = await p.chromium.launch_persistent_context(
                user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.pages[0]
            await Stealth().apply_stealth_async(page)
            success = await perform_login(page)
            return context, success

        browser_context, ok = await launch_and_login()
        semaphore = asyncio.Semaphore(concurrency)
        
        async def worker(url):
            async with semaphore:
                page = await browser_context.new_page()
                await Stealth().apply_stealth_async(page)
                try:
                    await page.goto(url, wait_until="load", timeout=90000)
                    await asyncio.sleep(7)
                    content = await page.content()
                    
                    # EAN
                    ean = "N/A"
                    ean_match = re.search(r'\b\d{13}\b', content)
                    if ean_match: ean = ean_match.group(0)
                    
                    # Titolo
                    soup = BeautifulSoup(content, 'lxml')
                    h1 = soup.select_one("h1.page-title, h1")
                    title = "N/A"
                    if h1:
                        h1_text = h1.get_text(strip=True)
                        title = h1_text.split("|")[1].strip() if "|" in h1_text else h1_text

                    c = conn.cursor()
                    c.execute("UPDATE products SET ean=?, title=?, last_updated=CURRENT_TIMESTAMP WHERE url=?", (ean, title, url))
                    conn.commit()
                    print(f"   ✅ FLUIDRA: {ean} | {title[:30]}")
                except Exception as e:
                    print(f"   ⚠️ Errore {url}: {str(e)[:40]}")
                finally:
                    await page.close()

        for i in range(0, len(todo_urls), vpn_rotate_every):
            batch = todo_urls[i:i+vpn_rotate_every]
            tasks = [worker(url) for url in batch]
            await asyncio.gather(*tasks)
            
            if i + vpn_rotate_every < len(todo_urls):
                await browser_context.close()
                rotate_mullvad()
                await asyncio.sleep(15)
                browser_context, ok = await launch_and_login()

        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(enrich_fluidra_turbo())
