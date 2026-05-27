import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    async with async_playwright() as p:
        # Try Firefox - sometimes less targeted by anti-bots
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
        )
        page = await context.new_page()
        
        # Test with the Lemon pool page
        url = 'https://www.grepool.com/it/piscine-in-legno/rettangolare/lemon-375-x-200-x-68-cm'
        print(f"Navigating to {url}...")
        
        try:
            # We use a very long timeout and wait for network idle
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            print(f"Response status: {response.status}")
            
            await asyncio.sleep(5) # Wait for potential redirects/challenges
            
            content = await page.content()
            if 'Incapsula' in content or 'incident_id' in content:
                print("❌ Blocked by Incapsula/Imperva.")
                # Look for the source of the blocked frame to see if we can extract info from URL params
                # But usually it's just a dead end.
            else:
                # Find image URLs in the source
                # Look for Fluidra DAM or Bynder links which Gre uses
                img_urls = re.findall(r'https://[^\s\"\'\)]+fluidra\.[^\s\"\'\)]+\.(?:jpg|png|webp)', content)
                img_urls = list(set(img_urls))
                
                if img_urls:
                    print(f"✅ Success! Found {len(img_urls)} official image URLs:")
                    for img in img_urls:
                        print(f"  - {img}")
                else:
                    print("⚠️ Page loaded but no Fluidra/Bynder images found.")
                    # Try general img tags
                    imgs = await page.query_selector_all('img')
                    print(f"Total img tags: {len(imgs)}")
                    for img in imgs[:10]:
                        src = await img.get_attribute('src')
                        print(f"  - {src}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
