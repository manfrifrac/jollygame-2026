import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def inspect_product():
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
        
        # Inspect Intex Ricambi product
        url = "https://www.intexricambi.it/ricambi/piscina-easy-set-pool-183m-x-51cm-28101np/"
        print(f"Inspecting Intex Ricambi product: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path="intex_ricambi_prod_debug.png")
            content = await page.content()
            with open("intex_ricambi_prod_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error: {e}")

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(inspect_product())
