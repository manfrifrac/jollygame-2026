import asyncio
from playwright.async_api import async_playwright
import json
import os
import urllib.parse
import random

WHITELIST = [
    'grepool.com', 'fluidra.com', 'juguetilandia', 'mercapool.com', 
    'piscinasdesmontables', 'habitium', 'leroymerlin', 'manomano', 
    'quimipool.com', 'poolaria.com', 'piscinaonline', 'bsvillage', 
    'grupposanmarco', 'amazon', 'ebay', 'pool-piscine', 'guide-piscine',
    'poolstore', 'piscines', 'naturclara', 'acsbrico', 'abitare',
    'pools.shop', 'poolplus', 'piscinayspa', 'poolomio', 'hornbach'
]

async def get_filtered_images(page, query):
    try:
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        items = await page.query_selector_all("a.iusc")
        img_urls = []
        
        for item in items[:50]: # Scan top 50 for official site matches
            m_attr = await item.get_attribute("m")
            if m_attr:
                data = json.loads(m_attr)
                murl = data.get("murl")
                purl = data.get("purl")
                
                if murl and purl:
                    # STRICT FILTER: ONLY grepool.com
                    if 'grepool.com' in purl.lower():
                        if 'logo' not in murl.lower() and 'icon' not in murl.lower():
                            img_urls.append(murl)
                        
        return list(set(img_urls))
    except Exception as e:
        print(f"Error for query {query}: {e}")
    return []

def update_web_data(results):
    try:
        # Filter out empty results for web
        web_data = {k: v for k, v in results.items() if v}
        web_path = 'image-reviewer-web/public/data.json'
        with open(web_path, 'w') as f:
            json.dump(web_data, f)
        print(f"  [Web] Updated {web_path} with {len(web_data)} products.")
    except Exception as e:
        print(f"  [Web] Error updating data: {e}")

async def main():
    with open('gre_missing_ean_map.json', 'r') as f:
        ean_map = json.load(f)
    
    output_file = 'gre_images_safe_final.json'
    results = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            results = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        skus = list(ean_map.keys())
        total = len(skus)
        
        for i, sku in enumerate(skus):
            # If we already have 3+ images, skip
            if sku in results and len(results[sku]) >= 3:
                print(f"[{i+1}/{total}] Already have enough images for {sku}")
                continue
                
            data = ean_map[sku]
            ean = data['ean']
            title = data['title']
            
            print(f"[{i+1}/{total}] Deep official search for {sku}...")
            
            # Priority queries
            queries = [
                f"site:grepool.com {sku}", # Try to get images indexed from official site
                f"site:fluidra.com {sku}",
                f"Gre {sku} gallery",
                f"Piscina Gre {ean} images",
                f"Gre {title[:60]}"
            ]
            
            all_images = []
            for query in queries:
                print(f"  Searching: {query}")
                images = await get_filtered_images(page, query)
                if images:
                    all_images.extend(images)
                    # If we found at least 5 different ones, that's enough
                    if len(set(all_images)) >= 6:
                        break
            
            # Filter duplicates and keep top 10
            unique_images = list(set(all_images))
            results[sku] = unique_images[:10]
            
            print(f"  ✅ Total verified images for {sku}: {len(results[sku])}")
                
            if (i + 1) % 10 == 0:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=4)
                update_web_data(results)
            
            await page.wait_for_timeout(random.randint(1000, 2000))
            
        await browser.close()
        
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    update_web_data(results)
    print("\nDeep safe scrape completed.")

if __name__ == "__main__":
    asyncio.run(main())
