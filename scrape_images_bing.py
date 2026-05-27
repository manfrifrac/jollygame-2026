import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os

async def get_image_from_bing(page, query):
    try:
        search_url = f"https://www.bing.com/images/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        # Click on the first image result to get a better view or just grab the thumb if it's large enough
        # Actually, Bing images search results have metadata in the 'm' attribute of the 'a' tag
        first_result = await page.query_selector("a.iusc")
        if first_result:
            m_attr = await first_result.get_attribute("m")
            if m_attr:
                data = json.loads(m_attr)
                return data.get("murl") # murl is the original image URL
    except Exception as e:
        print(f"Error searching for {query}: {e}")
    return None

async def main():
    df = pd.read_csv('prodotti_gre_mancanti.csv')
    # Filter out header if present
    df = df[df['sku'] != 'ARTICOLO']
    
    # We will also need EANs for better search. Let's merge with the listino data
    listino_df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    # Create a mapping SKU -> EAN
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
        
        # Test with first 15 products
        count = 0
        for _, row in df.iterrows():
            sku = str(row['sku']).strip().upper()
            title = str(row['title']).strip()
            ean = sku_to_ean.get(sku, "")
            
            # Search query: SKU + "Gre" or EAN
            search_query = f"Gre {sku} {ean}"
            print(f"Searching for: {search_query}")
            
            img_url = await get_image_from_bing(page, search_query)
            if img_url:
                print(f"  Found: {img_url}")
                results[sku] = [img_url]
            else:
                # Try with title if SKU/EAN fails
                print(f"  No image found for SKU, trying title...")
                img_url = await get_image_from_bing(page, f"Gre {title[:50]}")
                if img_url:
                    print(f"    Found by title: {img_url}")
                    results[sku] = [img_url]
                else:
                    results[sku] = []
            
            count += 1
            if count >= 15:
                break
            
            await page.wait_for_timeout(1000) # Be polite
            
        await browser.close()
        
    with open('gre_missing_images_bing.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("\nScrape completed. Results saved to gre_missing_images_bing.json")

if __name__ == "__main__":
    asyncio.run(main())
