import asyncio
from playwright.async_api import async_playwright
import re

async def test_locales():
    locales = [
        'https://www.grepool.com/en/wooden-pools/rectangular/lemon-375-x-200-x-68-cm',
        'https://www.grepool.com/es/piscinas-de-madera/rectangular/lemon-375-x-200-x-68-cm',
        'https://www.grepool.com/fr/piscines-bois/rectangulaire/lemon-375-x-200-x-68-cm'
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for url in locales:
            page = await browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
            print(f"Testing: {url}")
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)
                content = await page.content()
                if 'Incapsula' in content:
                    print(f"  ❌ Blocked (Incapsula)")
                elif 'incident_id' in content:
                    print(f"  ❌ Blocked (Incident ID)")
                else:
                    print(f"  ✅ Success!")
                    dam_links = re.findall(r'https://dam\.fluidra\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', content)
                    print(f"  Found {len(set(dam_links))} DAM links.")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_locales())
