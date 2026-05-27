import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup
import json
import re

async def random_delay(min_s=2, max_s=5):
    """Attesa casuale per simulare un umano."""
    await asyncio.sleep(random.uniform(min_s, max_s))

async def human_scroll(page):
    """Scrolla la pagina in modo non lineare."""
    for i in range(random.randint(2, 4)):
        scroll_amount = random.randint(300, 600)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(0.5, 1.5))

async def human_mouse_move(page):
    """Muove il mouse in punti casuali dello schermo."""
    width, height = 1920, 1080
    for i in range(3):
        x, y = random.randint(100, width-100), random.randint(100, height-100)
        await page.mouse.move(x, y, steps=10)
        await asyncio.sleep(random.uniform(0.2, 0.5))

async def scrape_deep_product_stealth(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        print(f"🚀 Avvio Stealth Scraper su: {url}")

        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Teniamo visibile per monitorare se appare un captcha
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            slow_mo=random.randint(200, 500) # Latenza tra i comandi
        )

        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Monitoraggio Risposte per rilevare Blocchi
        page.on("response", lambda response: print(f"⚠️ BLOCCO RILEVATO (403/429)!") if response.status in [403, 429] else None)

        data = {"url": url, "main_info": {}, "spare_parts": [], "documents": []}

        try:
            print("Navigazione...")
            await page.goto(url, wait_until="load", timeout=90000)
            await random_delay(5, 8) # Attesa lunga post-caricamento
            
            await human_mouse_move(page)
            await human_scroll(page)

            # --- 1. INFO PRODOTTO ---
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # EAN
            ean_search = re.search(r'EAN:\s*(\d+)', content)
            data['main_info']['ean'] = ean_search.group(1) if ean_search else "N/A"
            
            # Prezzi
            prices = soup.select(".price-container .price")
            data['main_info']['net_price'] = prices[0].get_text(strip=True) if len(prices) > 0 else "N/A"
            data['main_info']['list_price'] = prices[1].get_text(strip=True) if len(prices) > 1 else "N/A"

            # --- 2. TAB ESPLOSO ---
            print("Apertura Esploso...")
            try:
                # Muoviamo il mouse sopra la tab prima di cliccare
                target = page.locator(".data.item.title", has_text="Esploso")
                if await target.count() > 0:
                    await target.hover()
                    await random_delay(1, 2)
                    await target.click()
                    print("Clic effettuato su Esploso.")
                    await random_delay(4, 6)
                    
                    # Estrazione ricambi (Selettori più generici per sicurezza)
                    part_soup = BeautifulSoup(await page.content(), 'lxml')
                    for item in part_soup.select(".product-item-info, tr.item"):
                        sku = item.select_one(".sku, [data-sku], td:nth-child(2)")
                        name = item.select_one(".name, .product-item-name, td:nth-child(3)")
                        price = item.select_one(".price, td:nth-child(5)")
                        if sku and name:
                            data['spare_parts'].append({
                                "sku": sku.get_text(strip=True) if sku.get_text() else sku.get('data-sku'),
                                "name": name.get_text(strip=True),
                                "price": price.get_text(strip=True) if price else "N/A"
                            })
            except Exception as e:
                print(f"Errore Esploso: {e}")

            # --- 3. TAB DOCUMENTI ---
            print("Apertura Documenti...")
            try:
                target_doc = page.locator(".data.item.title", has_text="Documenti")
                if await target_doc.count() > 0:
                    await target_doc.hover()
                    await random_delay(1, 2)
                    await target_doc.click()
                    await random_delay(3, 5)
                    
                    doc_soup = BeautifulSoup(await page.content(), 'lxml')
                    for a in doc_soup.find_all('a', href=True):
                        if ".pdf" in a['href'].lower():
                            data['documents'].append({
                                "name": a.get_text(strip=True), 
                                "url": a['href'] if a['href'].startswith('http') else "https://pro.fluidra.com" + a['href']
                            })
            except Exception as e:
                print(f"Errore Documenti: {e}")

            print("\n✅ Scraping Completato con Successo.")
            print(f"Trovati {len(data['spare_parts'])} ricambi e {len(data['documents'])} documenti.")

            with open("cnx_50_iq_stealth.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Errore Fatale: {e}")
        finally:
            print("Chiusura sicura...")
            await browser_context.close()

if __name__ == "__main__":
    url = "https://pro.fluidra.com/it_it/1284501-cnx-50-iq.html"
    asyncio.run(scrape_deep_product_stealth(url))
