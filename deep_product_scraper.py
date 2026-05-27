import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup
import json
import re
import sqlite3

# Configurazione Cartelle
os.makedirs("downloads/images", exist_ok=True)
os.makedirs("downloads/docs", exist_ok=True)

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
            price_net=excluded.price_net,
            price_list=excluded.price_list,
            stock_italy=excluded.stock_italy,
            stock_spain=excluded.stock_spain,
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

def link_spare(conn, parent_sku, child_sku, index):
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO product_relations (parent_sku, child_sku, diagram_index) VALUES (?, ?, ?)', (parent_sku.strip(), child_sku.strip(), index))

async def deep_scrape_product(page, url, conn):
    print(f"🔍 Scansione: {url}")
    try:
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(8)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        data = {"url": url, "sku": "N/A", "is_spare": 0}
        
        # 1. SKU e TITOLO ESTESO
        h1 = soup.select_one("h1.page-title span, h1.page-title")
        if h1:
            h1_text = h1.get_text(strip=True)
            if "|" in h1_text:
                parts = h1_text.split("|")
                data['sku'] = parts[0].strip()
                data['title'] = " ".join(parts[1:]).strip() # Tutto quello dopo la prima pipe
            else:
                data['title'] = h1_text
        
        if data['sku'] == "N/A":
            sku_box = soup.select_one(".product-info-stock-sku .value, .sku .value")
            if sku_box: data['sku'] = sku_box.get_text(strip=True)

        print(f"   🆔 SKU: {data['sku']} | 🏷️ TITOLO: {data.get('title')}")
        if data['sku'] == "N/A" or len(data['sku']) < 3: return

        ean_search = re.search(r'EAN:\s*(\d+)', content)
        data['ean'] = ean_search.group(1) if ean_search else "N/A"

        prices = soup.select(".price-container .price")
        data['price_net'] = clean_price(prices[0].get_text(strip=True)) if len(prices) > 0 else 0.0
        data['price_list'] = clean_price(prices[1].get_text(strip=True)) if len(prices) > 1 else 0.0
        
        # Stock
        data['stock_italy'] = 0
        data['stock_spain'] = 0
        for s in soup.select(".stock-item"):
            txt = s.get_text(strip=True)
            count = int(re.search(r'\((\d+)\)', txt).group(1)) if re.search(r'\((\d+)\)', txt) else 0
            if "Italia" in txt: data['stock_italy'] = count
            if "Spagna" in txt: data['stock_spain'] = count

        data['taxonomy'] = " > ".join([li.get_text(strip=True) for li in soup.select(".breadcrumbs li")])
        data['images'] = [img.get('src') for img in soup.select(".fotorama__img, .gallery-placeholder img") if img.get('src') and "placeholder" not in img.get('src')]
        data['docs'] = [{"name": a.get_text(strip=True), "url": a['href']} for a in soup.find_all('a', href=True) if ".pdf" in a['href'].lower()]

        upsert_product(conn, data)
        conn.commit()

        # --- 2. RICAMBI ---
        spare_tab = page.locator(".data.item.title", has_text="Esploso")
        if await spare_tab.count() > 0:
            print(f"   ⚙️  Scarico ricambi...")
            await spare_tab.click()
            await asyncio.sleep(5)
            
            spare_soup = BeautifulSoup(await page.content(), 'lxml')
            spare_items = spare_soup.select(".spare-container-fix-item")
            for item in spare_items:
                s_sku = item.get('data-sku')
                s_name = item.get('data-name') # Contiene già lo SKU e il Nome (es. "R0516700 | VITE...")
                s_price = item.get('data-priceunformatted')
                s_fullprice = item.get('data-fullpriceunformatted')
                s_pos = item.get('data-position')
                s_url = item.get('data-producturl')
                if s_sku:
                    spare_data = {"sku": s_sku, "title": s_name, "price_net": clean_price(s_price), "price_list": clean_price(s_fullprice), "is_spare": 1, "url": s_url}
                    upsert_product(conn, spare_data)
                    link_spare(conn, data['sku'], s_sku, s_pos)
            conn.commit()
            print(f"   ✅ {len(spare_items)} ricambi salvati.")

    except Exception as e:
        print(f"   ❌ Errore: {e}")

async def main():
    conn = sqlite3.connect('fluidra_catalog.db')
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        await deep_scrape_product(page, "https://pro.fluidra.com/it_it/1284501-cnx-50-iq.html", conn)
        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
