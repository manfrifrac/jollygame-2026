import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os
import urllib.parse
import random

async def get_images_bing_stealth(page, sku, title):
    try:
        # Improved search query: specific for Gre pool liners/accessories
        query = f"Gre {sku} {title[:60]}"
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        items = await page.query_selector_all("a.iusc")
        img_urls = []
        for item in items[:5]:
            m_attr = await item.get_attribute("m")
            if m_attr:
                data = json.loads(m_attr)
                murl = data.get("murl")
                if murl and "http" in murl:
                    img_urls.append(murl)
        return img_urls
    except Exception as e:
        print(f"Error for {sku}: {e}")
    return []

async def main():
    df = pd.read_csv('prodotti_gre_mancanti.csv')
    df = df[df['sku'] != 'ARTICOLO']
    
    output_file = 'gre_missing_images_final.json'
    results = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            results = json.load(f)
    
    # Identify items that STILL need images (empty list or not in results)
    to_retry = []
    for _, row in df.iterrows():
        sku = str(row['sku']).strip().upper()
        if sku not in results or not results[sku]:
            to_retry.append({'sku': sku, 'title': str(row['title']).strip()})
            
    if not to_retry:
        print("All products have images or were already processed.")
        return

    print(f"Retrying {len(to_retry)} products without images...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        count = 0
        for item in to_retry:
            sku = item['sku']
            title = item['title']
            
            count += 1
            print(f"[{count}/{len(to_retry)}] Retrying Bing for {sku}...")
            images = await get_images_bing_stealth(page, sku, title)
            results[sku] = images
            if images:
                print(f"  Found {len(images)} images.")
            else:
                # Last resort: try searching ONLY by title if SKU is weird (like F790207)
                print(f"  No images for SKU, trying title only...")
                images = await get_images_bing_stealth(page, "", title[:80])
                results[sku] = images
                if images:
                     print(f"    Found {len(images)} images by title.")
                else:
                     print(f"    No images found.")
                
            if count % 10 == 0:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=4)
            
            await page.wait_for_timeout(random.randint(1000, 2500))
            
        await browser.close()
        
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print("\nRetry completed.")

if __name__ == "__main__":
    asyncio.run(main())
