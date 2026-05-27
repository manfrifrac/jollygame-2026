import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    async with async_playwright() as p:
        # WebKit is sometimes less detected as it's the engine for Safari
        browser = await p.webkit.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15'
        )
        
        url = 'https://www.grepool.com/it/piscine-in-legno/rettangolare/lemon-375-x-200-x-68-cm'
        print(f"Navigating to {url} using WebKit...")
        
        try:
            await page.goto(url, wait_until='load', timeout=60000)
            await asyncio.sleep(5)
            
            content = await page.content()
            if 'Incapsula' in content:
                print("❌ Blocked by Incapsula.")
            else:
                print("✅ SUCCESS! WebKit bypassed protection.")
                dam_links = re.findall(r'https://dam\.fluidra\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', content)
                print(f"Found {len(set(dam_links))} official images.")
                for img in set(dam_links):
                    print(f"  - {img}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
