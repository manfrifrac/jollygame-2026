import asyncio
from playwright.async_api import async_playwright
import json
import urllib.parse
import os

async def get_official_images(page, sku):
    try:
        # Search Bing specifically for official domains
        query = f'"{sku}" (site:grepool.com OR site:fluidra.com)'
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        items = await page.query_selector_all("a.iusc")
        img_urls = []
        for item in items:
            m_attr = await item.get_attribute("m")
            if m_attr:
                data = json.loads(m_attr)
                murl = data.get("murl") # Actual image URL
                purl = data.get("purl") # Source page URL
                
                # We want images hosted on official sites OR appearing on official pages
                if "grepool.com" in murl.lower() or "fluidra.com" in murl.lower() or \
                   "grepool.com" in purl.lower() or "fluidra.com" in purl.lower():
                    img_urls.append(murl)
                    
        return list(set(img_urls))
    except Exception as e:
        print(f"Error for {sku}: {e}")
    return []

async def main():
    # Test with a few products
    skus = ["790204", "KITPROV613", "786641", "KIT730GY"]
    for sku in skus:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            print(f"Searching official images for {sku}...")
            imgs = await get_official_images(page, sku)
            print(f"  Found {len(imgs)} official images.")
            for img in imgs:
                print(f"    - {img}")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
