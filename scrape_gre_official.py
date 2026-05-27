import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import json
import re

async def get_official_images_via_ddg(page, sku):
    try:
        query = f"site:grepool.com {sku}"
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&iax=images&ia=images"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        # Regex to find official Magento product images
        # Structure is usually /media/catalog/product/...
        matches = re.findall(r'https://www.grepool.com/media/catalog/product/[^\s\"\'\)]+\.jpg', content)
        # Also check for .png and higher res versions
        matches += re.findall(r'https://www.grepool.com/media/catalog/product/[^\s\"\'\)]+\.png', content)
        
        return list(set(matches))
    except Exception as e:
        print(f"Error on DDG for {sku}: {e}")
    return []

async def main():
    skus = ['790204', 'KITPROV613', '786641']
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for sku in skus:
            print(f"Searching official images for {sku}...")
            imgs = await get_official_images_via_ddg(page, sku)
            results[sku] = imgs
            print(f"  Found {len(imgs)} images on grepool.com")
            for img in imgs:
                print(f"    - {img}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
