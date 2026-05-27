import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
from bs4 import BeautifulSoup

async def extract_categories():
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
        
        print("Navigating to Fluidra Pro Home...")
        try:
            await page.goto("https://pro.fluidra.com/it_it/", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # The dropdown might need a click or hover, but the user provided the HTML already rendered.
            # Let's see if we can find the links in the current page source.
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            categories = []
            # Based on user snippet, categories are in <li class="... ui-menu-item"> or similar
            # Searching for catalog/category/view/s/
            for a in soup.find_all('a', href=True):
                href = a['href']
                if "/catalog/category/view/s/" in href:
                    label = a.get_text(strip=True)
                    categories.append({"label": label, "url": href})
            
            # Dedup
            unique_categories = {c['url']: c for c in categories}.values()
            unique_categories = sorted(unique_categories, key=lambda x: x['label'])
            
            print(f"Found {len(unique_categories)} category links.")
            
            with open("fluidra_categories.json", "w", encoding="utf-8") as f:
                json.dump(list(unique_categories), f, indent=4)
            print("Categories saved to fluidra_categories.json")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    asyncio.run(extract_categories())
