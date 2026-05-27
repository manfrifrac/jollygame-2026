import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        sku = "790204"
        # Search for the SKU on the official DAM domain
        query = f'"{sku}" site:dam.fluidra.com'
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
        print(f"Searching DDG: {url}")
        
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        
        # Look for the dam.fluidra.com pattern
        # Pattern: https://dam.fluidra.com/m/HASH/Medium-SKU.jpg
        matches = re.findall(r'https://dam.fluidra.com/m/[0-9a-fA-F]+/Medium-[^\s\"\'\)]+\.jpg', content)
        print(f"Found {len(set(matches))} official DAM links.")
        for m in set(matches):
            print(f"  - {m}")
            
        # Fallback: look for ANY dam.fluidra.com link
        if not matches:
             matches = re.findall(r'https://dam.fluidra.com/[^\s\"\'\)]+', content)
             print(f"Found {len(set(matches))} general DAM links.")
             for m in set(matches):
                 print(f"  - {m}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
