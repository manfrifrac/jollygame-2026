import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import sqlite3
import json
from deep_product_scraper import deep_scrape_product

async def run_multi_test():
    conn = sqlite3.connect('fluidra_catalog.db')
    test_urls = [
        "https://pro.fluidra.com/it_it/640256-1.html",
        "https://pro.fluidra.com/it_it/646605-2-gradino-luxe-1-gradino-di-sicurezza.html",
        "https://pro.fluidra.com/it_it/1005651-adattatore-tubo-pulitore-skimmer.html"
    ]

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)

        for url in test_urls:
            print(f"\n🚀 TEST SU: {url}")
            await deep_scrape_product(page, url, conn)
            await asyncio.sleep(5)

        await browser_context.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(run_multi_test())
