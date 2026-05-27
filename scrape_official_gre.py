import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
import re
import random

async def extract_images_from_url(page, url):
    print(f"  🚀 Scaning: {url}")
    try:
        await page.goto(url, wait_until="load", timeout=60000)
        await asyncio.sleep(5)
        
        content = await page.content()
        if 'Incapsula' in content:
            print("    ❌ Blocked.")
            return []
            
        # Extract official images (Fluidra DAM / Bynder)
        img_urls = re.findall(r'https://[^\s\"\'\)]+fluidra\.[^\s\"\'\)]+\.(?:jpg|png|webp)', content)
        
        # Also check style attributes (for background-image)
        gallery_elements = await page.query_selector_all(".gallery__image")
        for el in gallery_elements:
            style = await el.get_attribute("style")
            if style and "url(" in style:
                match = re.search(r'url\((.*?)\)', style)
                if match:
                    img_urls.append(match.group(1).strip("'\""))
        
        # Cleanup
        img_urls = list(set([u for u in img_urls if "loader" not in u and "logo" not in u]))
        return img_urls
    except Exception as e:
        print(f"    ❌ Error: {e}")
    return []

async def main():
    with open('gre_official_map_deep.json', 'r') as f:
        url_map = json.load(f)
    
    output_file = 'gre_official_images_final.json'
    results = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            results = json.load(f)
            
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), 'playwright_user_data')
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        # Warm up
        print("🌍 Warming up...")
        await page.goto("https://www.grepool.com/", wait_until="load", timeout=90000)
        await asyncio.sleep(20)
        
        skus = list(url_map.keys())
        total = len(skus)
        
        for i, sku in enumerate(skus):
            if sku in results and results[sku]:
                print(f"[{i+1}/{total}] Skipping {sku} (found)")
                continue
                
            url = url_map[sku]
            print(f"[{i+1}/{total}] SKU: {sku}")
            
            images = await extract_images_from_url(page, url)
            results[sku] = images
            print(f"    ✅ Found {len(images)} official images.")
            
            # Periodic save
            if (i + 1) % 5 == 0:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=4)
                # Also update web data for the user to see
                web_data = {k: v for k, v in results.items() if v}
                with open('image-reviewer-web/public/data.json', 'w') as f:
                    json.dump(web_data, f)
            
            await page.wait_for_timeout(random.randint(3000, 7000))
            
        await browser_context.close()
        
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print("\nOfficial scrape completed.")

if __name__ == "__main__":
    asyncio.run(main())
