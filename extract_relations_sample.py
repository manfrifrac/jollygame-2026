import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
from bs4 import BeautifulSoup

async def extract_relations_sample(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if next_data_script:
            pj = json.loads(next_data_script.string)
            pageProps = pj.get("props", {}).get("pageProps", {})
            
            print(f"Product: {pageProps.get('product', {}).get('sku')}")
            
            spareParts = pageProps.get("spareParts", [])
            relatedProducts = pageProps.get("relatedProducts", [])
            
            print(f"\nSpare Parts ({len(spareParts)}):")
            for sp in spareParts[:5]:
                print(f" - {sp.get('sku')}: {sp.get('name')}")
                
            print(f"\nRelated Products ({len(relatedProducts)}):")
            for rp in relatedProducts[:5]:
                print(f" - {rp.get('sku')}: {rp.get('name')}")
                
            # Let's save a full sample
            with open("sample_relations.json", "w", encoding="utf-8") as f:
                json.dump({"spareParts": spareParts, "relatedProducts": relatedProducts}, f, indent=2)
        
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(extract_relations_sample("https://it.bestway.eu/p/filtro-a-sabbia-8327-l-h"))
