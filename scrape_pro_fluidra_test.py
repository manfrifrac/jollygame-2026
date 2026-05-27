import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json

async def search_pro_fluidra(page, query):
    url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={query}"
    print(f"Searching Fluidra Pro for: {query}")
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Check results
        items = await page.query_selector_all(".product-item")
        print(f"  Found {len(items)} items.")
        
        if items:
            # Click first item
            link = await items[0].query_selector("a.product-item-photo")
            if link:
                href = await link.get_attribute("href")
                print(f"  Navigating to product: {href}")
                await page.goto(href, wait_until="networkidle", timeout=30000)
                
                # Extract gallery images
                # Based on previous knowledge, Fluidra Pro uses a standard gallery
                imgs = await page.query_selector_all(".gallery-placeholder img, .fotorama__img")
                img_urls = []
                for img in imgs:
                    src = await img.get_attribute("src")
                    if src and "http" in src and "loader" not in src:
                        img_urls.append(src)
                return list(set(img_urls))
    except Exception as e:
        print(f"  Error searching for {query}: {e}")
    return []

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), 'playwright_user_data')
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        # Try a few queries
        queries = ["790204", "Sunbay Lemon", "KITPROV613", "Bora Bora"]
        results = {}
        for q in queries:
            images = await search_pro_fluidra(page, q)
            results[q] = images
            print(f"  Extracted {len(images)} images.")
            
        await browser_context.close()
        
    with open('pro_fluidra_images_test.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
