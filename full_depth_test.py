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
    if isinstance(price_str, (int, float)): return float(price_str)
    p = str(price_str).replace("€", "").strip()
    if "," in p and "." in p: p = p.replace(".", "").replace(",", ".")
    elif "," in p: p = p.replace(",", ".")
    try: return float(re.sub(r'[^\d.]', '', p))
    except: return 0.0

def upsert_product(conn, data):
    cursor = conn.cursor()
    sku = data['sku'].strip()
    cursor.execute('''
        INSERT INTO products (sku, ean, title, description, price_net, price_list, discount, stock_italy, stock_spain, taxonomy, images_json, docs_json, videos_json, specs_json, url, is_spare_part)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sku) DO UPDATE SET
            ean=COALESCE(excluded.ean, ean),
            title=COALESCE(excluded.title, title),
            description=COALESCE(excluded.description, description),
            price_net=excluded.price_net,
            price_list=excluded.price_list,
            stock_italy=excluded.stock_italy,
            stock_spain=excluded.stock_spain,
            specs_json=excluded.specs_json,
            images_json=excluded.images_json,
            docs_json=excluded.docs_json,
            url=COALESCE(excluded.url, url),
            last_updated=CURRENT_TIMESTAMP
    ''', (
        sku, data.get('ean'), data.get('title'), data.get('description'),
        data.get('price_net', 0.0), data.get('price_list', 0.0), data.get('discount'),
        data.get('stock_italy', 0), data.get('stock_spain', 0), data.get('taxonomy'),
        json.dumps(data.get('images', [])), json.dumps(data.get('docs', [])),
        json.dumps(data.get('videos', [])), json.dumps(data.get('specs', {})),
        data.get('url'), data.get('is_spare', 0)
    ))

async def deep_scrape_full_test(url):
    conn = sqlite3.connect('fluidra_catalog.db')
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"🚀 TEST DI PROFONDITÀ TOTALE: {url}")
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(10)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        data = {"url": url, "sku": "N/A", "is_spare": 0}
        
        # 1. Identificativi
        sku_box = soup.select_one(".product-info-stock-sku .value, [itemprop='sku']")
        data['sku'] = sku_box.get_text(strip=True) if sku_box else "N/A"
        
        h1 = soup.select_one("h1.page-title")
        h1_text = h1.get_text(strip=True) if h1 else ""
        if "|" in h1_text:
            data['title'] = h1_text.split("|")[1].strip()
            if data['sku'] == "N/A": data['sku'] = h1_text.split("|")[0].strip()
        else:
            data['title'] = h1_text

        ean_match = re.search(r'EAN:\s*(\d+)', content)
        data['ean'] = ean_match.group(1) if ean_match else "N/A"

        # 2. Commerciale
        prices = soup.select(".price-container .price")
        data['price_net'] = clean_price(prices[0].get_text(strip=True)) if len(prices) > 0 else 0.0
        data['price_list'] = clean_price(prices[1].get_text(strip=True)) if len(prices) > 1 else 0.0
        data['discount'] = soup.select_one(".product__discount").get_text(strip=True) if soup.select_one(".product__discount") else "0%"

        # 3. Logistica (Stock Italia)
        data['stock_italy'] = 0
        data['stock_spain'] = 0
        for s in soup.select(".stock-item"):
            txt = s.get_text(strip=True)
            num = re.search(r'\((\d+)\)', txt)
            count = int(num.group(1)) if num else 0
            if "Italia" in txt: data['stock_italy'] = count
            if "Spagna" in txt: data['stock_spain'] = count

        # 4. Descrizione e Specifiche
        desc_box = soup.select_one(".product.attribute.description .value")
        data['description'] = str(desc_box) if desc_box else "" # Prendiamo l'HTML della descrizione

        specs = {}
        # Cerca tabelle tecniche (solitamente caricate via JS o in tab)
        for row in soup.select("table#product-attribute-specs-table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td: specs[th.get_text(strip=True)] = td.get_text(strip=True)
        data['specs'] = specs

        # 5. Asset e Documenti
        data['images'] = [img.get('src') for img in soup.select(".fotorama__img, .gallery-placeholder img") if img.get('src') and "placeholder" not in img.get('src')]
        data['docs'] = [{"name": a.get_text(strip=True), "url": a['href']} for a in soup.find_all('a', href=True) if ".pdf" in a['href'].lower()]

        # 6. Video
        videos = []
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and ("youtube" in src or "vimeo" in src): videos.append(src)
        data['videos'] = videos

        # Salva
        upsert_product(conn, data)
        conn.commit()

        print("\n--- RISULTATI TEST ---")
        print(f"SKU: {data['sku']}")
        print(f"Prezzo Netto: {data['price_net']} €")
        print(f"Stock Italia: {data['stock_italy']}")
        print(f"Documenti: {len(data['docs'])}")
        print(f"Video: {len(data['videos'])}")
        print(f"Specifiche: {len(data['specs'])} campi trovati.")

        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(deep_scrape_full_test("https://pro.fluidra.com/it_it/1284501-cnx-50-iq.html"))
