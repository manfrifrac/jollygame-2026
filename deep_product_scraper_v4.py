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
    title = data.get('title', 'N/A').strip()
    
    # Se il titolo è ancora N/A o troppo corto, proviamo a usare lo SKU o il meta title
    if title == "N/A" or len(title) < 2:
        title = f"Prodotto {sku}"

    if data.get('is_discontinued'):
        if "FUORI PRODUZIONE" not in title.upper():
            title = f"[FUORI PRODUZIONE] {title}"

    # Nota: Usiamo l'UPDATE per assicurarci di sovrascrivere i vecchi "N/A"
    cursor.execute('''
        INSERT INTO products (sku, ean, title, description, price_net, price_list, discount, stock_italy, stock_spain, taxonomy, images_json, docs_json, videos_json, specs_json, url, is_spare_part, diagram_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sku) DO UPDATE SET
            ean=COALESCE(excluded.ean, ean),
            title=CASE WHEN title = 'N/A' OR title LIKE 'Prodotto %' THEN excluded.title ELSE title END,
            description=COALESCE(excluded.description, description),
            price_net=excluded.price_net,
            stock_italy=excluded.stock_italy,
            diagram_url=COALESCE(excluded.diagram_url, diagram_url),
            last_updated=CURRENT_TIMESTAMP
    ''', (
        sku, data.get('ean'), title, data.get('description'),
        data.get('price_net', 0.0), data.get('price_list', 0.0), data.get('discount'),
        data.get('stock_italy', 0), data.get('stock_spain', 0), data.get('taxonomy'),
        json.dumps(data.get('images', [])), json.dumps(data.get('docs', [])),
        json.dumps(data.get('videos', [])), json.dumps(data.get('specs', {})),
        data.get('url'), data.get('is_spare', 0), data.get('diagram_url')
    ))

def link_spare(conn, parent_sku, child_sku, index):
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO product_relations (parent_sku, child_sku, diagram_index) VALUES (?, ?, ?)', (parent_sku.strip(), child_sku.strip(), index))

async def deep_scrape_final(page, url, conn):
    print(f"🔍 Scansione: {url}")
    try:
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(8)

        # Iniezione JS potenziata per Titolo e SKU
        page_info = await page.evaluate('''() => {
            let sku = document.querySelector('[itemprop="sku"]')?.innerText || 
                      document.querySelector('.product-info-stock-sku .value')?.innerText;
            
            let title = document.querySelector('h1.page-title span')?.innerText || 
                        document.querySelector('h1.page-title')?.innerText || 
                        document.querySelector('.base')?.innerText ||
                        document.title.split('|')[0].trim();
            
            let isDiscontinued = document.body.innerText.toLowerCase().includes("fuori produzione") || 
                                 document.body.innerText.toLowerCase().includes("discontinued");
            
            let diagImg = document.querySelector('.spare-map img#map')?.src || 
                          document.querySelector('.spare-map img')?.src;
            
            return { sku, title, isDiscontinued, diagImg };
        }''')

        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        data = {
            "url": url, 
            "sku": page_info['sku'] or "N/A", 
            "title": page_info['title'] or "N/A",
            "is_spare": 0,
            "is_discontinued": page_info['isDiscontinued'],
            "diagram_url": page_info['diagImg'],
            "description": ""
        }
        
        if data['sku'] == "N/A":
            url_part = url.split("/")[-1].split("-")[0]
            if len(url_part) >= 4: data['sku'] = url_part

        # Pulizia Titolo: Rimuovi lo SKU se presente nel titolo o la pipe
        t = data['title']
        if "|" in t:
            t = t.split("|")[1].strip()
        if data['sku'] != "N/A" and data['sku'] in t:
            t = t.replace(data['sku'], "").replace("-", "").strip()
        data['title'] = t

        print(f"   🆔 SKU: {data['sku']} | 🏷️ Titolo: {data['title']} | 🚫 Fuori Prod: {data['is_discontinued']}")

        # Stock Italia
        it_match = re.search(r'Italia\s*\((\d+)\)', content, re.IGNORECASE)
        data['stock_italy'] = int(it_match.group(1)) if it_match else 0
        
        # Prezzi
        prices = soup.select(".price-container .price")
        data['price_net'] = clean_price(prices[0].get_text(strip=True)) if len(prices) > 0 else 0.0

        # Assets
        data['images'] = [img.get('src') for img in soup.select(".fotorama__img, .gallery-placeholder img") if img.get('src') and "placeholder" not in img.get('src')]
        data['docs'] = [{"name": a.get_text(strip=True), "url": a['href']} for a in soup.find_all('a', href=True) if ".pdf" in a['href'].lower()]

        upsert_product(conn, data)
        conn.commit()

        # --- RICAMBI ---
        spare_tab = page.locator(".data.item.title", has_text="Esploso")
        if await spare_tab.count() > 0:
            await spare_tab.click()
            await asyncio.sleep(5)
            spare_soup = BeautifulSoup(await page.content(), 'lxml')
            for item in spare_soup.select(".spare-container-fix-item"):
                s_info = {attr: item.get(attr) for attr in item.attrs if attr.startswith('data-')}
                s_sku = s_info.get('data-sku')
                if s_sku:
                    full_name = s_info.get('data-name', s_sku)
                    s_title = full_name.split("|")[1].strip() if "|" in full_name else full_name
                    spare_data = {
                        "sku": s_sku, "title": s_title,
                        "price_net": clean_price(s_info.get('data-priceunformatted')),
                        "is_spare": 1, "url": s_info.get('data-producturl'),
                        "is_discontinued": False
                    }
                    upsert_product(conn, spare_data)
                    link_spare(conn, data['sku'], s_sku, s_info.get('data-position'))
            conn.commit()

    except Exception as e:
        print(f"   ❌ Errore: {e}")

if __name__ == "__main__":
    pass
