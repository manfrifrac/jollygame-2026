import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os

async def get_images_from_habitium(page, ean):
    try:
        url = f"https://habitium.it/catalogsearch/result/?q={ean}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Check if we are on a product page or search results
        if "catalogsearch" in page.url:
            # Click first product
            item = await page.query_selector(".product-item-info a")
            if item:
                await item.click()
                await page.wait_for_load_state("networkidle")
        
        # Now on product page (ideally)
        images = await page.query_selector_all(".gallery-placeholder img, .fotorama__img, .product.media img")
        img_urls = []
        for img in images:
            src = await img.get_attribute("src")
            if src and "http" in src and "loader" not in src:
                img_urls.append(src)
        return list(set(img_urls))
    except Exception as e:
        print(f"Error on Habitium for {ean}: {e}")
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
            ean = sku_to_ean.get(sku)
            if not ean: continue
            
            print(f"Searching Habitium for SKU {sku} (EAN {ean})...")
            images = await get_images_from_habitium(page, ean)
            if images:
                print(f"  Found {len(images)} images.")
                results[sku] = images
            else:
                print(f"  No images found.")
                results[sku] = []
                
            count += 1
            if count >= 10: break
            
        await browser.close()
        
    with open('gre_images_habitium.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
