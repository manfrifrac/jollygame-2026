import asyncio
import csv
import json
import sqlite3
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

async def scrape_gre_rescue():
    db_path = "fluidra_clean.db"
    csv_path = "mapping_prodotti_jolly_gre.csv"
    
    if not os.path.exists(csv_path):
        print("CSV Gre non trovato.")
        return

    # Leggiamo gli SKU e URL
    gre_tasks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Grepool_URL']:
                gre_tasks.append({"sku": row['SKU'], "url": row['Grepool_URL']})

    print(f"🚀 Inizio recupero di {len(gre_tasks)} prodotti Gre...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for i, task in enumerate(gre_tasks):
            print(f"[{i+1}/{len(gre_tasks)}] Scansione Gre: {task['url']}")
            try:
                await page.goto(task['url'], wait_until="load", timeout=60000)
                await asyncio.sleep(3)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Estrazione Dati
                title = soup.select_one('h1').get_text(strip=True) if soup.select_one('h1') else ""
                
                # EAN: spesso nel testo o specifiche
                ean = ""
                ean_match = re.search(r'EAN:\s*(\d{13})', content)
                if ean_match: ean = ean_match.group(1)
                
                # Prezzo
                price_box = soup.select_one('.price, .current-price, [data-price-amount]')
                price = 0.0
                if price_box:
                    p_text = price_box.get_text(strip=True).replace('€', '').replace('.', '').replace(',', '.')
                    try: price = float(re.sub(r'[^\d.]', '', p_text))
                    except: pass
                
                # Immagini
                imgs = [img['src'] for img in soup.select('img.product-image, .gallery img') if 'http' in img.get('src', '')]
                
                # Descrizione
                desc = soup.select_one('.product-description, #description')
                desc_html = desc.decode_contents() if desc else ""

                # Upsert nel DB Fluidra (Gre è parte di Fluidra)
                cursor.execute('''
                    INSERT INTO products (sku, title, ean, price_list, description, images_json, url, is_spare_part, taxonomy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sku) DO UPDATE SET
                        title = excluded.title,
                        ean = COALESCE(NULLIF(excluded.ean, ''), ean),
                        price_list = excluded.price_list,
                        description = excluded.description,
                        images_json = excluded.images_json,
                        taxonomy = 'Piscine in Acciaio > Gre'
                ''', (task['sku'], title, ean, price, desc_html, json.dumps(imgs), task['url'], 0, 'Piscine in Acciaio > Gre'))
                
                conn.commit()
                print(f"   ✅ Salvato: {title} | EAN: {ean} | Prezzo: {price}")
                
            except Exception as e:
                print(f"   ❌ Errore su {task['url']}: {e}")

        await browser.close()
    conn.close()
    print("\n🎉 Recupero Gre completato.")

if __name__ == "__main__":
    asyncio.run(scrape_gre_rescue())
