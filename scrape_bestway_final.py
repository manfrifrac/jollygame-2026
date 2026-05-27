import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup
import json
import sqlite3
import time

# Caricamento categorie scoperte
def get_categories():
    try:
        with open("bestway_discovered_categories.json", "r") as f:
            return json.load(f)
    except:
        return [
            "https://it.bestway.eu/catalog/piscine-fuori-terra",
            "https://it.bestway.eu/catalog/idromassaggio-gonfiabile-lay-z-spa"
        ]

def save_to_db(data):
    if not data or not data.get('SKU'):
        return
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO bestway_products 
    (sku, ean, title, price, description_html, bullet_points, category, images, video, url, specs_json, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        data['SKU'], data['EAN'], data['Title'], data['Price'], 
        data['Description_HTML'], data['Bullet_Points'], data['Category'],
        data['Images'], data['Video'], data['URL'], data['Specs_JSON']
    ))
    conn.commit()
    conn.close()

async def get_product_links(browser_context, category_url):
    page = await browser_context.new_page()
    await Stealth().apply_stealth_async(page)
    print(f"Scansione categoria: {category_url}")
    links = set()
    try:
        await page.goto(category_url, wait_until="networkidle", timeout=60000)
        while True:
            load_more = await page.query_selector("button:has-text('Carica altri'), button:has-text('Mostra altri')")
            if load_more and await load_more.is_visible():
                await load_more.click()
                await page.wait_for_timeout(2000)
            else:
                break
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("/p/"):
                links.add(f"https://it.bestway.eu{href}")
    except Exception as e:
        print(f"Errore scansione categoria {category_url}: {e}")
    finally:
        await page.close()
    return list(links)

async def scrape_product_details(browser_context, url):
    page = await browser_context.new_page()
    await Stealth().apply_stealth_async(page)
    data = {}
    try:
        # Check if already scraped to avoid double work
        conn = sqlite3.connect('bestway_catalog.db')
        cursor = conn.cursor()
        cursor.execute("SELECT sku FROM bestway_products WHERE url = ?", (url,))
        if cursor.fetchone():
            conn.close()
            await page.close()
            return None
        conn.close()

        await page.goto(url, wait_until="networkidle", timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        if next_data_script:
            pj = json.loads(next_data_script.string)
            prod = pj.get("props", {}).get("pageProps", {}).get("product", {})
            data = {
                "URL": url,
                "Title": prod.get("name"),
                "SKU": prod.get("sku"),
                "EAN": prod.get("ean"),
                "Price": prod.get("price", {}).get("value"),
                "Description_HTML": prod.get("descriptionHtml"),
                "Bullet_Points": prod.get("bulletPoints"),
                "Images": ",".join([img.get("url") for img in prod.get("images", []) if img.get("url")]),
                "Video": next((img.get("videoUrl") for img in prod.get("images", []) if img.get("videoUrl")), ""),
                "Category": " > ".join(prod.get("categories", [])),
                "Specs_JSON": json.dumps({k: v for k, v in prod.items() if isinstance(v, (str, int, float)) and k not in ['name', 'descriptionHtml', 'bulletPoints', 'path', 'slug']}, ensure_ascii=False)
            }
            save_to_db(data)
            print(f"Salvato: {data['Title']} ({data['SKU']})")
    except Exception as e:
        print(f"Errore prodotto {url}: {e}")
    finally:
        await page.close()
    return data

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        CATEGORIES = get_categories()
        all_product_urls = set()
        for cat in CATEGORIES:
            urls = await get_product_links(browser_context, cat)
            for u in urls: all_product_urls.add(u)
        
        all_product_urls = list(all_product_urls)
        print(f"Totale prodotti da scaricare: {len(all_product_urls)}")
        
        batch_size = 5
        for i in range(0, len(all_product_urls), batch_size):
            batch = all_product_urls[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(all_product_urls)//batch_size)+1}...")
            await asyncio.gather(*[scrape_product_details(browser_context, url) for url in batch])
            await asyncio.sleep(1)

        await browser_context.close()
        print("\nScraping completato!")

if __name__ == "__main__":
    asyncio.run(main())
