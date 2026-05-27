import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
from bs4 import BeautifulSoup

async def scrape_intex_details():
    with open("intex_product_links.json", "r", encoding="utf-8") as f:
        product_links = json.load(f)

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        results = []
        
        # Load existing progress if any
        if os.path.exists("intex_full_catalog.json"):
            with open("intex_full_catalog.json", "r", encoding="utf-8") as f:
                results = json.load(f)
        
        processed_urls = {item["url"] for item in results}

        async def safe_goto(url, retries=3):
            for i in range(retries):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(3000)
                    return True
                except Exception as e:
                    if i == retries - 1: return False
                    await asyncio.sleep(2)
            return False

        # --- Scrape Intex Italia ---
        print(f"Scraping {len(product_links['intex_italia'])} Intex Italia products...")
        for url in product_links["intex_italia"]:
            if url in processed_urls: continue
            
            print(f" Scraping: {url}")
            if await safe_goto(url):
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                title = soup.select_one('h1.product_title')
                sku = soup.select_one('.sku')
                description = soup.select_one('.woocommerce-product-details__short-description, .product-short-description')
                full_desc = soup.select_one('#tab-description')
                
                images = []
                img_tags = soup.select('.woocommerce-product-gallery__image img')
                for img in img_tags:
                    src = img.get('data-large_image') or img.get('data-src') or img.get('src')
                    if src and src not in images:
                        images.append(src)
                
                results.append({
                    "source": "intex_italia",
                    "url": url,
                    "title": title.get_text(strip=True) if title else "",
                    "sku": sku.get_text(strip=True) if sku else "",
                    "short_description": description.get_text(strip=True) if description else "",
                    "description": full_desc.get_text(strip=True) if full_desc else "",
                    "images": images,
                    "spare_parts": []
                })
                
                # Intermediate save
                if len(results) % 5 == 0:
                    with open("intex_full_catalog.json", "w", encoding="utf-8") as f:
                        json.dump(results, f, indent=4)
            processed_urls.add(url)

        # --- Scrape Intex Ricambi ---
        print(f"\nScraping {len(product_links['intex_ricambi'])} Intex Ricambi products...")
        for url in product_links["intex_ricambi"]:
            if url in processed_urls: continue
            
            print(f" Scraping: {url}")
            if await safe_goto(url):
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                title = soup.select_one('h1.product_title')
                sku = soup.select_one('.sku')
                
                images = []
                img_tags = soup.select('.woocommerce-product-gallery__image img')
                for img in img_tags:
                    src = img.get('data-large_image') or img.get('data-src') or img.get('src')
                    if src and src not in images:
                        images.append(src)

                # Extract spare parts table
                spare_parts = []
                rows = soup.select('table.wc-product-table tbody tr')
                for row in rows:
                    ref = row.select_one('.col-key')
                    part_sku = row.select_one('.col-sku')
                    part_name = row.select_one('.col-name a')
                    part_price = row.select_one('.col-price .amount')
                    part_stock = row.select_one('.col-stock')
                    
                    if part_sku and part_name:
                        spare_parts.append({
                            "ref": ref.get_text(strip=True) if ref else "",
                            "sku": part_sku.get_text(strip=True),
                            "name": part_name.get_text(strip=True),
                            "url": part_name['href'],
                            "price": part_price.get_text(strip=True) if part_price else "",
                            "stock": part_stock.get_text(strip=True) if part_stock else ""
                        })
                
                results.append({
                    "source": "intex_ricambi",
                    "url": url,
                    "title": title.get_text(strip=True) if title else "",
                    "sku": sku.get_text(strip=True) if sku else "",
                    "images": images,
                    "spare_parts": spare_parts
                })
                
                # Intermediate save
                if len(results) % 5 == 0:
                    with open("intex_full_catalog.json", "w", encoding="utf-8") as f:
                        json.dump(results, f, indent=4)
            processed_urls.add(url)

        with open("intex_full_catalog.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        print(f"\nScraping complete. Saved {len(results)} products to intex_full_catalog.json")

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(scrape_intex_details())
