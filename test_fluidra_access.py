import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_access():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        print(f"Using user data dir: {user_data_dir}")
        
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True, # Use headless=True for CLI compatibility
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print("Navigating to Fluidra Pro...")
        try:
            await page.goto("https://pro.fluidra.com/it_it/", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            
            title = await page.title()
            print(f"Page Title: {title}")
            
            # Check if we see logout button or username to confirm login
            content = await page.content()
            is_logged_in = "log out" in content.lower() or "esci" in content.lower() or "mio account" in content.lower()
            print(f"Logged in check (keyword search): {is_logged_in}")
            
            # Take a screenshot to verify
            await page.screenshot(path="fluidra_access_test.png")
            print("Screenshot saved as fluidra_access_test.png")
            
            # Save a bit of HTML to see the structure
            with open("fluidra_debug.html", "w", encoding="utf-8") as f:
                f.write(content[:10000]) # first 10k chars
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    asyncio.run(test_access())
