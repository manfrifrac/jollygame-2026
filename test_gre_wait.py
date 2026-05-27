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
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        # Search by EAN
        ean = '3605217902047'
        url = f'https://www.grepool.com/catalogsearch/result/?q={ean}'
        
        try:
            print("🏠 Warming up cookies on Home...")
            await page.goto("https://www.grepool.com/", wait_until="load", timeout=90000)
            await asyncio.sleep(15)
            
            print(f"🚀 Searching EAN: {ean}...")
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(5)
            
            content = await page.content()
            if 'Incapsula' in content:
                print("❌ Blocked.")
            else:
                print("✅ Search Page Loaded.")
                
                # Check for product items
                items = await page.query_selector_all(".product-item-info a")
                print(f"🔎 Found {len(items)} product items.")
                
                if items:
                    href = await items[0].get_attribute("href")
                    print(f"🔗 Product URL found: {href}")
                    await page.goto(href, wait_until="load", timeout=30000)
                    await asyncio.sleep(10) # Wait for gallery
                    
                    final_content = await page.content()
                    img_urls = re.findall(r'https://[^\s\"\'\)]+fluidra\.[^\s\"\'\)]+\.(?:jpg|png|webp)', final_content)
                    img_urls = list(set([u for u in img_urls if "loader" not in u and "logo" not in u]))
                    
                    print(f"🖼️ Found {len(img_urls)} official images.")
                    for img in img_urls:
                        print(f"  - {img}")
                else:
                    print("⚠️ No products found for this EAN.")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(run())
