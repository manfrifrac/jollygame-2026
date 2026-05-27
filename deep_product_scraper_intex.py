import asyncio
import json
import sqlite3
import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

DB_FILE = "intex_deep_catalog.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            url TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            sku TEXT,
            ean TEXT,
            price TEXT,
            short_description TEXT,
            images TEXT,
            pdfs TEXT,
            categories TEXT,
            attributes TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

async def scrape_product(page, url, source, conn):
    try:
        print(f"Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")
        
        data = {
            "url": url,
            "source": source,
            "title": "",
            "sku": "",
            "ean": "",
            "price": "",
            "short_description": "",
            "images": [],
            "pdfs": [],
            "categories": [],
            "attributes": {}
        }
        
        # JSON-LD Extraction for exact SKU/EAN/Price/Title
        json_lds = soup.find_all('script', type='application/ld+json')
        for script in json_lds:
            if not script.string: continue
            try:
                ld_data = json.loads(script.string)
                if isinstance(ld_data, dict):
                    ld_data = [ld_data]
                for item in ld_data:
                    if isinstance(item, dict):
                        if "@graph" in item:
                            for graph_item in item["@graph"]:
                                if graph_item.get("@type") == "Product":
                                    data["title"] = graph_item.get("name", data["title"])
                                    data["sku"] = graph_item.get("sku", data["sku"])
                                    data["ean"] = graph_item.get("gtin", graph_item.get("gtin13", data["ean"]))
                                    if "offers" in graph_item:
                                        offers = graph_item["offers"]
                                        if isinstance(offers, list) and len(offers) > 0:
                                            if "priceSpecification" in offers[0]:
                                                ps = offers[0]["priceSpecification"]
                                                if isinstance(ps, list) and len(ps) > 0:
                                                    data["price"] = str(ps[0].get("price", ""))
                                            else:
                                                data["price"] = str(offers[0].get("price", ""))
                        elif item.get("@type") == "Product":
                            data["title"] = item.get("name", data["title"])
                            data["sku"] = item.get("sku", data["sku"])
                            data["ean"] = item.get("gtin", item.get("gtin13", data["ean"]))
                            if "offers" in item:
                                offers = item["offers"]
                                if isinstance(offers, list) and len(offers) > 0:
                                    data["price"] = str(offers[0].get("price", ""))
                                elif isinstance(offers, dict):
                                    data["price"] = str(offers.get("price", ""))
            except Exception as e:
                pass

        # Fallbacks via HTML
        if not data["title"]:
            title_elem = soup.select_one("h1.product_title")
            if title_elem: data["title"] = title_elem.get_text(strip=True)
            
        if not data["price"]:
            price_elem = soup.select_one("p.price .woocommerce-Price-amount bdi")
            if price_elem: data["price"] = price_elem.get_text(strip=True)
            
        if not data["sku"]:
            sku_elem = soup.select_one(".sku")
            if sku_elem: data["sku"] = sku_elem.get_text(strip=True)
            
        if not data["ean"]:
            ean_elem = soup.select_one(".ean") or soup.find(string=lambda t: t and "EAN" in t)
            if ean_elem:
                raw_ean = ean_elem.parent.get_text(strip=True) if hasattr(ean_elem, "parent") else ean_elem.strip()
                data["ean"] = raw_ean.replace("EAN:", "").replace("EAN", "").strip()

        short_desc_elem = soup.select_one(".woocommerce-product-details__short-description")
        if short_desc_elem:
            data["short_description"] = short_desc_elem.get_text(separator="\n", strip=True)
            
        images = soup.select(".woocommerce-product-gallery__image a")
        data["images"] = [img.get("href") for img in images if img.get("href")]
        
        pdfs = soup.select('a[href$=".pdf"]')
        data["pdfs"] = [pdf.get("href") for pdf in pdfs if pdf.get("href")]
        
        cats = soup.select(".posted_in a")
        data["categories"] = [cat.get_text(strip=True) for cat in cats]
        
        tech_table = soup.select_one("table.woocommerce-product-attributes")
        if tech_table:
            for row in tech_table.select("tr"):
                th = row.select_one("th")
                td = row.select_one("td")
                if th and td:
                    data["attributes"][th.get_text(strip=True)] = td.get_text(strip=True)
                    
        # Clean up formats
        data["ean"] = str(data["ean"]).replace("None", "").strip() if data["ean"] else ""
        data["sku"] = str(data["sku"]).replace("None", "").strip() if data["sku"] else ""

        # Insert into DB
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO products (url, source, title, sku, ean, price, short_description, images, pdfs, categories, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data["url"], data["source"], data["title"], data["sku"], data["ean"], data["price"],
            data["short_description"], json.dumps(data["images"]), json.dumps(data["pdfs"]),
            json.dumps(data["categories"]), json.dumps(data["attributes"])
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"  Error on {url}: {e}")
        return False

async def main():
    conn = init_db()
    
    with open("intex_product_links.json", "r", encoding="utf-8") as f:
        links_data = json.load(f)
        
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM products")
    scraped_urls = set(row[0] for row in cursor.fetchall())
    
    all_tasks = []
    for source, links in links_data.items():
        for link in links:
            all_tasks.append((source, link))
            
    pending_tasks = [t for t in all_tasks if t[1] not in scraped_urls]
    print(f"Total links: {len(all_tasks)}. Already scraped: {len(scraped_urls)}. Pending: {len(pending_tasks)}")
    
    if not pending_tasks:
        print("All done!")
        conn.close()
        return

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data_deep")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        for i, (source, url) in enumerate(pending_tasks):
            print(f"[{i+1}/{len(pending_tasks)}] ", end="")
            for attempt in range(3):
                success = await scrape_product(page, url, source, conn)
                if success:
                    break
                print(f"  Retrying ({attempt+1}/3)...")
                await asyncio.sleep(2)
            
            await asyncio.sleep(0.5)
            
        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
