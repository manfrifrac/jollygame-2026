import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def inspect():
    url = "https://www.intexitalia.com/piscine-fuori-terra/piscina-ovale-prisma-frame-610x305x122cm-26798np/"
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
        
        print(f"Navigating to {url}")
        for i in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(5000)
                break
            except Exception as e:
                print(f"Retry {i+1} failed: {e}")
                await asyncio.sleep(2)
        
        # Expand any accordions or tabs if necessary
        try:
            tabs = await page.locator(".accordion-header, .nav-link, .tab-title, .woocommerce-Tabs-panel").all()
            for tab in tabs:
                await tab.click(timeout=1000)
                await page.wait_for_timeout(500)
        except:
            pass
                
        html = await page.content()
        with open("sample_product.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("HTML saved to sample_product.html")
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(inspect())
