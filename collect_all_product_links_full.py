import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup
import json

async def collect_links_full():
    with open("fluidra_categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    output_file = "fluidra_product_links_map.json"
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            all_products = json.load(f)
    else:
        all_products = {}

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True, # Headless per il background
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)

        for cat in categories:
            cat_name = cat['label']
            cat_url = cat['url']
            
            if cat_name in all_products: continue

            print(f"📂 Elaborazione: {cat_name}")
            links_in_cat = []
            current_page_url = cat_url
            
            while current_page_url:
                try:
                    await page.goto(current_page_url, wait_until="load", timeout=60000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'lxml')
                    
                    for a in soup.select("a.product-item-link"):
                        href = a['href']
                        if href not in links_in_cat: links_in_cat.append(href)
                    
                    next_page = soup.select_one("a.action.next")
                    current_page_url = next_page['href'] if next_page and next_page.get('href') else None
                
                except Exception as e:
                    print(f"   ❌ Errore: {e}")
                    current_page_url = None

            all_products[cat_name] = links_in_cat
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_products, f, indent=4, ensure_ascii=False)
            
            await asyncio.sleep(random.uniform(5, 10))

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(collect_links_full())
