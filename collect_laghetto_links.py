import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import json

async def collect_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        base_url = "https://www.piscinelaghetto.com"
        categories = [
            "/product_category/piscine-fuori-terra-rigide",
            "/product_category/piscine-fuori-terra-morbide",
            "/product_category/piscine-seminterrate",
            "/product_category/piscine-interrate",
            "/product_category/minipiscine"
        ]
        
        product_links = set()
        
        for cat in categories:
            url = base_url + cat
            print(f"Scraping category: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/product/' in href and href.startswith(base_url):
                        # Clean URL
                        clean_url = href.split('?')[0].split('#')[0].rstrip('/')
                        if clean_url != base_url + "/product":
                            product_links.add(clean_url)
            except Exception as e:
                print(f"Error on {url}: {e}")

        print(f"Found {len(product_links)} products.")
        with open("laghetto_links.json", "w") as f:
            json.dump(list(product_links), f, indent=4)
        print("Links saved to laghetto_links.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(collect_links())
