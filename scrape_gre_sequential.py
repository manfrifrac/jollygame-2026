import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import re

async def run():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), 'playwright_user_data')
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        # 1. Warm up with Google
        print("🌍 Warming up with Google...")
        await page.goto("https://www.google.com/search?q=Gre+pools+official+site", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 2. Go to Gre home
        print("🏠 Navigating to Gre Home...")
        await page.goto("https://www.grepool.com/it/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        # 3. Go to product page
        url = 'https://www.grepool.com/it/piscine-in-legno/rettangolare/lemon-375-x-200-x-68-cm'
        print(f"🚀 Navigating to Product: {url}...")
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(5)
            
            content = await page.content()
            if 'Incapsula' in content:
                print("❌ Blocked by Incapsula.")
            else:
                print("✅ SUCCESS!")
                img_urls = re.findall(r'https://dam\.fluidra\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', content)
                img_urls += re.findall(r'https://fluidra\.bynder\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', content)
                img_urls = list(set(img_urls))
                print(f"🖼️ Found {len(img_urls)} official image URLs.")
                for img in img_urls:
                    print(f"  - {img}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(run())
