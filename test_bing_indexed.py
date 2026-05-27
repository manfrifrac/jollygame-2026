import asyncio
from playwright.async_api import async_playwright
import json
import urllib.parse

async def get_indexed_official_images(page, query):
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
    print(f"Searching Bing for indexed Grepool images: {query}")
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        items = await page.query_selector_all("a.iusc")
        img_urls = []
        for item in items[:20]:
            m_attr = await item.get_attribute("m")
            if m_attr:
                data = json.loads(m_attr)
                murl = data.get("murl") # Image URL
                purl = data.get("purl") # Source Page
                
                # Check if it comes from Grepool
                if "grepool.com" in purl.lower():
                    img_urls.append(murl)
        return list(set(img_urls))
    except Exception as e:
        print(f"Error: {e}")
    return []

async def main():
    skus = ["790204", "KITPROV613", "786641"]
    for sku in skus:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Search by SKU restricted to site
            query = f'site:grepool.com "{sku}"'
            imgs = await get_indexed_official_images(page, query)
            print(f"Found {len(imgs)} indexed images for {sku}")
            for img in imgs:
                print(f"  - {img}")
            
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
