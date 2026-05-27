import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup
import json
import re
import sqlite3

def clean_price(price_str):
    if not price_str or price_str == "N/A": return 0.0
    p = str(price_str).replace("€", "").strip()
    if "," in p and "." in p: p = p.replace(".", "").replace(",", ".")
    elif "," in p: p = p.replace(",", ".")
    try: return float(re.sub(r'[^\d.]', '', p))
    except: return 0.0

async def deep_scrape_full_v3(url):
    conn = sqlite3.connect('fluidra_catalog.db')
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"🚀 TEST DI PROFONDITÀ V3 (JSON PARSING): {url}")
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(10)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        data = {"url": url, "sku": "N/A", "title": "N/A", "ean": "N/A", "is_spare": 0}

        # 1. PARSING JSON-LD (Lo standard Google)
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                js = json.loads(s.string)
                # Può essere una lista o un dict
                items = js if isinstance(js, list) else [js]
                for item in items:
                    if item.get('@type') == 'Product':
                        data['sku'] = item.get('sku', data['sku'])
                        data['title'] = item.get('name', data['title'])
                        data['description'] = item.get('description', "")
                        if item.get('gtin13'): data['ean'] = item.get('gtin13')
                        print("   ✅ Dati trovati in JSON-LD!")
            except:
                pass

        # 2. PARSING MAGENTO INIT (Dati grezzi interni)
        if data['sku'] == "N/A":
            scripts = soup.find_all("script", type="text/x-magento-init")
            for s in scripts:
                if "Magento_Catalog/js/product/view/provider" in s.string:
                    try:
                        js = json.loads(s.string)
                        # Navighiamo nel labirinto Magento
                        for key in js:
                            if "data" in js[key]:
                                prod_data = js[key]["data"]
                                data['sku'] = prod_data.get('sku', data['sku'])
                                data['title'] = prod_data.get('name', data['title'])
                                print("   ✅ Dati trovati in Magento Init!")
                    except:
                        pass

        # 3. STOCK E PREZZI (Già funzionanti in V2)
        stock_text = soup.get_text()
        it_match = re.search(r'Italia\s*\((\d+)\)', stock_text, re.IGNORECASE)
        data['stock_italy'] = int(it_match.group(1)) if it_match else 0
        
        prices = soup.select(".price-container .price")
        data['price_net'] = clean_price(prices[0].get_text(strip=True)) if len(prices) > 0 else 0.0

        # Specifiche (Se non sono nel JSON, le cerchiamo nel testo)
        specs = {}
        for row in soup.select("table.additional-attributes tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td: specs[th.get_text(strip=True)] = td.get_text(strip=True)
        data['specs'] = specs

        print("\n--- RISULTATI TEST V3 ---")
        print(f"SKU: {data['sku']}")
        print(f"TITOLO: {data['title']}")
        print(f"EAN: {data['ean']}")
        print(f"Stock Italia: {data['stock_italy']}")
        print(f"Prezzo Netto: {data['price_net']} €")
        print(f"Specifiche: {len(data['specs'])} campi.")

        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(deep_scrape_full_v3("https://pro.fluidra.com/it_it/1284501-cnx-50-iq.html"))
