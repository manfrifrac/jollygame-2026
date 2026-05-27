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

async def deep_scrape_full_v2(url):
    conn = sqlite3.connect('fluidra_catalog.db')
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"🚀 TEST DI PROFONDITÀ V2: {url}")
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(10)

        # 1. FORZIAMO IL CARICAMENTO DELLE TAB
        print("Espansione tab informative...")
        tab_selectors = [".data.item.title", "#tab-label-additional-title", "#tab-label-spareparts-title"]
        for sel in tab_selectors:
            try:
                tabs = await page.query_selector_all(sel)
                for tab in tabs:
                    await tab.click()
                    await asyncio.sleep(1)
            except:
                pass
        
        await asyncio.sleep(3) # Tempo per popolare il DOM
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        data = {"url": url, "sku": "N/A", "is_spare": 0}
        
        # --- ESTRAZIONE DATI ---
        
        # SKU Principale (Cerca ovunque)
        sku_targets = [
            soup.select_one(".product-info-stock-sku .value"),
            soup.select_one("[itemprop='sku']"),
            soup.select_one(".sku .value")
        ]
        for target in sku_targets:
            if target and target.get_text(strip=True):
                data['sku'] = target.get_text(strip=True)
                break
        
        # Titolo
        h1 = soup.select_one("h1.page-title")
        if h1:
            h1_text = h1.get_text(strip=True)
            if "|" in h1_text:
                parts = h1_text.split("|")
                if data['sku'] == "N/A": data['sku'] = parts[0].strip()
                data['title'] = parts[1].strip()
            else:
                data['title'] = h1_text

        # EAN
        ean_match = re.search(r'EAN:\s*(\d+)', content)
        data['ean'] = ean_match.group(1) if ean_match else "N/A"

        # Prezzi
        prices = soup.select(".price-container .price")
        data['price_net'] = clean_price(prices[0].get_text(strip=True)) if len(prices) > 0 else 0.0
        data['price_list'] = clean_price(prices[1].get_text(strip=True)) if len(prices) > 1 else 0.0

        # Stock Italia (Regex migliorata)
        data['stock_italy'] = 0
        data['stock_spain'] = 0
        stock_text = soup.get_text()
        it_match = re.search(r'Italia\s*\((\d+)\)', stock_text, re.IGNORECASE)
        es_match = re.search(r'Spagna\s*\((\d+)\)', stock_text, re.IGNORECASE)
        if it_match: data['stock_italy'] = int(it_match.group(1))
        if es_match: data['stock_spain'] = int(es_match.group(1))

        # Descrizione (HTML pulito)
        desc_box = soup.select_one(".product.attribute.description .value")
        data['description'] = str(desc_box) if desc_box else ""

        # Specifiche Tecniche
        specs = {}
        for row in soup.select("table.data.table.additional-attributes tr, table#product-attribute-specs-table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td: specs[th.get_text(strip=True)] = td.get_text(strip=True)
        data['specs'] = specs

        # Documenti
        data['docs'] = [{"name": a.get_text(strip=True), "url": a['href']} for a in soup.find_all('a', href=True) if ".pdf" in a['href'].lower()]

        # Immagini
        data['images'] = [img.get('src') for img in soup.select(".fotorama__img, .gallery-placeholder img") if img.get('src') and "placeholder" not in img.get('src')]

        print("\n--- RISULTATI TEST V2 ---")
        print(f"SKU: {data['sku']}")
        print(f"Prezzo Netto: {data['price_net']} €")
        print(f"Stock Italia: {data['stock_italy']}")
        print(f"Specifiche: {len(data['specs'])} campi.")
        print(f"EAN: {data['ean']}")

        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(deep_scrape_full_v2("https://pro.fluidra.com/it_it/1284501-cnx-50-iq.html"))
