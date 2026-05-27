import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os
import urllib.parse
import random

async def get_images_bing_stealth(page, sku, title):
    try:
        # Search for SKU and title to be specific
        query = f"Gre {sku} {title[:30]}"
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Bing stores image data in the 'm' attribute of 'a.iusc'
        items = await page.query_selector_all("a.iusc")
        img_urls = []
        for item in items[:3]: # Take top 3
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
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        total = len(df)
        count = 0
        for _, row in df.iterrows():
            sku = str(row['sku']).strip().upper()
            title = str(row['title']).strip()
            
            count += 1
            if sku in results and results[sku]:
                print(f"[{count}/{total}] Skipping {sku} (already found)")
                continue
            
            print(f"[{count}/{total}] Searching Bing for {sku}...")
            images = await get_images_bing_stealth(page, sku, title)
            results[sku] = images
            if images:
                print(f"  Found {len(images)} images.")
            else:
                print(f"  No images found.")
                
            # Periodic save
            if count % 10 == 0:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=4)
            
            await page.wait_for_timeout(random.randint(1000, 3000))
            
        await browser.close()
        
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print("\nScrape completed.")

if __name__ == "__main__":
    asyncio.run(main())
