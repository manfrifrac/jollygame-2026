
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def scan_all():
    df = pd.read_csv("mapping_prodotti_jolly_gre_FINALE.csv")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        found_products = []
        for index, row in df.iterrows():
            url = row['Grepool_URL']
            sku = row['SKU']
            print(f"[{index+1}/{len(df)}] Scanning {sku}...")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                content = await page.content()
                if 'jollygame' in content.lower():
                    print(f"  [FOUND] JollyGame mentioned in {sku}")
                    found_products.append({"SKU": sku, "URL": url})
            except:
                print(f"  [ERROR] Failed to load {sku}")
                
        await browser.close()
    
    if found_products:
        print("\nSummary of products with JollyGame mention:")
        for fp in found_products:
            print(f"- {fp['SKU']}: {fp['URL']}")
    else:
        print("\nNo mentions of JollyGame found in pre-rendered source.")

if __name__ == "__main__":
    asyncio.run(scan_all())
