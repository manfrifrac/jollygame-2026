import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
from bs4 import BeautifulSoup

async def extract_intex_categories():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        results = {
            "intex_italia": [],
            "intex_ricambi": []
        }

        # Extract from Intex Italia
        print("Extracting Intex Italia categories...")
        try:
            await page.goto("https://www.intexitalia.com/prodotti/", wait_until="networkidle", timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            items = soup.select('.list-categories .item')
            for item in items:
                a = item.find('a', href=True)
                title_tag = item.find(['h2', 'h3'])
                if a:
                    results["intex_italia"].append({
                        "label": title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True),
                        "url": a['href']
                    })
            print(f"Found {len(results['intex_italia'])} categories on Intex Italia.")
        except Exception as e:
            print(f"Error Intex Italia: {e}")

        # Extract from Intex Ricambi
        print("\nExtracting Intex Ricambi categories...")
        try:
            await page.goto("https://www.intexricambi.it/", wait_until="networkidle", timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            items = soup.select('.list-product_categories .item')
            for item in items:
                a = item.find('a', href=True)
                title_tag = item.find(['h2', 'h3'])
                if a:
                    results["intex_ricambi"].append({
                        "label": title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True),
                        "url": a['href']
                    })
            print(f"Found {len(results['intex_ricambi'])} categories on Intex Ricambi.")
        except Exception as e:
            print(f"Error Intex Ricambi: {e}")

        with open("intex_categories.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        print("\nCategories saved to intex_categories.json")

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(extract_intex_categories())
