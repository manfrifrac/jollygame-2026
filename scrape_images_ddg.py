import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os
import urllib.parse

async def get_image_from_ddg(page, query):
    try:
        # DDG images search with specific filters
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&iax=images&ia=images"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # In DDG, image results are in the tile
        # We can extract the 'data-src' or the original link if possible
        # Actually, DDG is hard to scrape directly. 
        # Let's try to get the first 5 images and filter by domain
        images = await page.query_selector_all("img.tile--img__img")
        results = []
        for img in images[:5]:
            src = await img.get_attribute("src")
            if src:
                if src.startswith("//"): src = "https:" + src
                results.append(src)
        return results
    except Exception as e:
        print(f"Error on DDG for {query}: {e}")
    return []

async def main():
    df = pd.read_csv('prodotti_gre_mancanti.csv')
    df = df[df['sku'] != 'ARTICOLO']
    
    listino_df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    sku_to_ean = {}
    for _, row in listino_df.iterrows():
        sku = str(row.iloc[6]).strip().upper()
        ean = str(row.iloc[9]).strip()
        if sku and ean:
            sku_to_ean[sku] = ean

    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Test first 10
        count = 0
        for _, row in df.iterrows():
            sku = str(row['sku']).strip().upper()
            ean = sku_to_ean.get(sku, "")
            title = str(row['title']).strip()
            
            # Very specific query
            query = f"Piscina Gre {sku} {ean}"
            print(f"Searching for: {query}")
            
            images = await get_image_from_ddg(page, query)
            if images:
                print(f"  Found {len(images)} images.")
                results[sku] = images
            else:
                print(f"  No images found.")
                results[sku] = []
                
            count += 1
            if count >= 10: break
            await page.wait_for_timeout(2000)
            
        await browser.close()
        
    with open('gre_images_ddg.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
