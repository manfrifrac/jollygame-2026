import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import os
from bs4 import BeautifulSoup

async def inspect_full_json(url):
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
            print("Root keys:", pj.keys())
            if 'props' in pj:
                print("Props keys:", pj['props'].keys())
                if 'pageProps' in pj['props']:
                    print("PageProps keys:", pj['props']['pageProps'].keys())
        
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(inspect_full_json("https://it.bestway.eu/p/parco-acquatico-turbo-splash-constant-air"))
