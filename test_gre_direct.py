import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import re

async def run():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), 'playwright_user_data')
        # Use persistent context to leverage existing sessions/cookies
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        # Test URL
        url = 'https://www.grepool.com/it/piscine-in-legno/rettangolare/lemon-375-x-200-x-68-cm'
        
        try:
            print("🏠 Navigating to home to establish session...")
            await page.goto("https://www.grepool.com/it/", wait_until="load", timeout=60000)
            await asyncio.sleep(5)
            
            print(f"🚀 Navigating to product: {url}...")
            await page.goto(url, wait_until='load', timeout=60000)
            await asyncio.sleep(5)
            
            content = await page.content()
            if 'Incapsula' in content or 'incident_id' in content:
                print("❌ Blocked by Incapsula.")
                # If blocked, maybe try to wait more or interact
            else:
                print("✅ SUCCESS! Page bypassed protection.")
                
                # Logic from debug_gre_source.html: images are in background-image of .gallery__image
                img_urls = []
                
                # Method 1: Regex on full content for DAM links
                dam_links = re.findall(r'https://dam\.fluidra\.com/m/[0-9a-fA-F]+/[^\s\"\'\)]+\.jpg', content)
                img_urls.extend(dam_links)
                
                # Method 2: Extract from style attribute
                gallery_elements = await page.query_selector_all(".gallery__image")
                for el in gallery_elements:
                    style = await el.get_attribute("style")
                    if style and "url(" in style:
                        match = re.search(r'url\((.*?)\)', style)
                        if match:
                            url_cleaned = match.group(1).strip("'\"")
                            img_urls.append(url_cleaned)
                
                img_urls = list(set(img_urls))
                print(f"🖼️ Found {len(img_urls)} official images:")
                for img in img_urls:
                    print(f"  - {img}")
                    
        except Exception as e:
            print(f"❌ Error during navigation: {e}")
            
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(run())
