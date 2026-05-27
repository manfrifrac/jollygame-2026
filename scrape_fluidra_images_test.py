import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
import urllib.parse

async def search_fluidra(page, sku):
    encoded_sku = urllib.parse.quote(sku)
    search_url = f"https://pro.fluidra.com/it_it/catalogsearch/result/?q={encoded_sku}"
    
    print(f"[{sku}] Navigating to {search_url}")
    await page.goto(search_url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)
    
    # Check if there are results
    items = await page.query_selector_all('.product-item')
    if not items:
         print(f"[{sku}] No results on Fluidra.")
         return []
         
    print(f"[{sku}] Found results, extracting first product link...")
    first_link = await items[0].query_selector('a.product-item-photo')
    if not first_link:
        return []
        
    href = await first_link.get_attribute('href')
    if href:
        print(f"[{sku}] Navigating to product page: {href}")
        await page.goto(href, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Extract images from fotorama or gallery
        img_urls = []
        images = await page.query_selector_all('.fotorama__img')
        if not images:
            images = await page.query_selector_all('.gallery-placeholder img, .product-image-photo')
            
        for img in images:
            src = await img.get_attribute('src')
            if src and 'loader' not in src:
                 img_urls.append(src)
                 
        return list(set(img_urls))
    return []

async def main():
    skus_to_check = ["790204", "KIT500QGRE", "KIT300QGRE", "786641"]
    results = {}
    
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
        
        for sku in skus_to_check:
            images = await search_fluidra(page, sku)
            results[sku] = images
            print(f"[{sku}] Extracted images: {images}")
            
        await browser_context.close()
        
    with open('fluidra_images_test.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
