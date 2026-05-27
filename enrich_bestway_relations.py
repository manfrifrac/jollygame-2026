import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
import sqlite3
from bs4 import BeautifulSoup

def save_spare_part(sp_data):
    if not sp_data.get('sku'): return
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute("SELECT sku FROM bestway_products WHERE sku = ?", (sp_data['sku'],))
    if not cursor.fetchone():
        # Insert minimal data from JSON
        cursor.execute('''
        INSERT INTO bestway_products 
        (sku, title, price, images, url, category, specs_json, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            sp_data['sku'], 
            sp_data.get('name'), 
            sp_data.get('price', {}).get('value'),
            sp_data.get('image'),
            f"https://it.bestway.eu/p/{sp_data.get('slug')}" if sp_data.get('slug') else None,
            "Ricambi > " + (sp_data.get('name')[:20] if sp_data.get('name') else "Generale"),
            json.dumps(sp_data, ensure_ascii=False)
        ))
        print(f"  [+] Nuovo ricambio aggiunto: {sp_data['sku']}")
    
    conn.commit()
    conn.close()

def link_relation(parent_sku, child_sku, rel_type):
    if not parent_sku or not child_sku: return
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO product_relations (parent_sku, child_sku, relation_type) VALUES (?, ?, ?)", 
                   (parent_sku, child_sku, rel_type))
    conn.commit()
    conn.close()

async def enrich_product(browser_context, sku, url):
    page = await browser_context.new_page()
    await Stealth().apply_stealth_async(page)
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if next_data_script:
            pj = json.loads(next_data_script.string)
            pageProps = pj.get("props", {}).get("pageProps", {})
            
            # Spare Parts
            sparePartsGroups = pageProps.get("spareParts", [])
            for group in sparePartsGroups:
                for item in group.get("items", []):
                    sp_sku = item.get("sku")
                    if not sp_sku: sp_sku = item.get("id")
                    if sp_sku:
                        save_spare_part(item)
                        link_relation(sku, sp_sku, 'spare_part')
            
            # Related
            related = pageProps.get("relatedProducts", [])
            for item in related:
                rel_sku = item.get("sku")
                if rel_sku:
                    link_relation(sku, rel_sku, 'related')
                    
            print(f"Enriched: {sku} ({len(sparePartsGroups)} groups, {len(related)} related)")
    except Exception as e:
        print(f"Error enriching {sku}: {e}")
    finally:
        await page.close()

async def main():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    # Prendi 10 prodotti complessi non ancora processati (idealmente potremmo aggiungere un flag, ma per ora facciamo i primi 10)
    cursor.execute('''
    SELECT sku, url FROM bestway_products 
    WHERE (category LIKE "%Piscine%" OR category LIKE "%Pompe%" OR category LIKE "%Idromassaggio%")
    ''')
    targets = cursor.fetchall()
    conn.close()
    
    print(f"Inizio arricchimento di {len(targets)} prodotti...")
    
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        
        for sku, url in targets:
            await enrich_product(browser_context, sku, url)
            await asyncio.sleep(1)
            
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(main())
