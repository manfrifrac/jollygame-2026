import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import random
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Randomize viewport and user agent
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': random.randint(1024, 1920), 'height': random.randint(768, 1080)}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Disable tracking scripts if possible
        await page.route("**/*.{js,png,jpg,jpeg}", lambda route: route.abort() if "google-analytics" in route.request.url or "facebook" in route.request.url else route.continue_())
        
        url = 'https://www.grepool.com/it/piscine-in-legno/rettangolare/lemon-375-x-200-x-68-cm'
        print(f"Targeting: {url}")
        
        try:
            # Human-like navigation
            await page.goto("https://www.google.com", wait_until="load")
            await page.wait_for_timeout(2000)
            
            # Go to Gre site
            response = await page.goto(url, wait_until='load', timeout=60000)
            print(f"Status: {response.status}")
            
            # Slow scroll
            for i in range(5):
                await page.mouse.wheel(0, 500)
                await page.wait_for_timeout(1000)
            
            content = await page.content()
            if 'Incapsula' in content:
                print("❌ Blocked.")
            else:
                print("✅ Success!")
                # Find DAM links
                dam_links = re.findall(r'https://dam\.fluidra\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', content)
                print(f"Found {len(set(dam_links))} DAM links.")
                for l in set(dam_links):
                    print(f"  - {l}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
