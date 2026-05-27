import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def analyze_intex():
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
        
        # Test Intex Italia
        print("Testing Intex Italia (Prodotti)...")
        try:
            await page.goto("https://www.intexitalia.com/prodotti/", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"Intex Italia Title: {title}")
            
            await page.screenshot(path="intex_italia_debug.png")
            content = await page.content()
            with open("intex_italia_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Intex Italia analysis saved.")
            
        except Exception as e:
            print(f"Error Intex Italia: {e}")

        # Test Intex Ricambi
        print("\nTesting Intex Ricambi...")
        try:
            await page.goto("https://www.intexricambi.it/", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"Intex Ricambi Title: {title}")
            
            await page.screenshot(path="intex_ricambi_debug.png")
            content = await page.content()
            with open("intex_ricambi_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Intex Ricambi analysis saved.")
            
        except Exception as e:
            print(f"Error Intex Ricambi: {e}")

        finally:
            await browser_context.close()

if __name__ == "__main__":
    asyncio.run(analyze_intex())
