import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
from bs4 import BeautifulSoup

async def inspect_spare_parts_structure(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"Opening {url}...")
        await page.goto(url, wait_until="networkidle")
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if next_data_script:
            pj = json.loads(next_data_script.string)
            pageProps = pj.get("props", {}).get("pageProps", {})
            product = pageProps.get("product", {})
            
            # Print all root keys in pageProps and product
            print("\nKeys in pageProps:", pageProps.keys())
            print("Keys in product:", product.keys())
            
            # Check for specific interesting keys
            interesting_keys = ['relatedProducts', 'crossSell', 'upSell', 'accessories', 'spareParts', 'components', 'kit']
            for key in interesting_keys:
                if key in product:
                    print(f"\nFOUND '{key}' in product:")
                    print(json.dumps(product[key], indent=2)[:1000] + "...")
                if key in pageProps:
                    print(f"\nFOUND '{key}' in pageProps:")
                    print(json.dumps(pageProps[key], indent=2)[:1000] + "...")
                    
            # Let's save the whole pageProps to a file for manual review
            with open("bestway_product_debug_full.json", "w", encoding="utf-8") as f:
                json.dump(pageProps, f, indent=2, ensure_ascii=False)
            print("\nFull pageProps saved to bestway_product_debug_full.json")
        else:
            print("No __NEXT_DATA__ found.")
            
        await browser_context.close()

if __name__ == "__main__":
    # Use a product that likely has spare parts
    asyncio.run(inspect_spare_parts_structure("https://it.bestway.eu/p/58497-7"))
