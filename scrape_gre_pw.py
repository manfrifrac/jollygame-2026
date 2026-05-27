import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json

def clean_sku(sku):
    if pd.isna(sku) or str(sku).strip().upper() == 'ARTICOLO':
        return None
    return str(sku).strip()

async def search_and_extract(page, sku):
    try:
        encoded_sku = sku # Playwright handles URL encoding automatically if we type it
        print(f"[{sku}] Navigating to search...")
        
        # Go to home first to set cookies if needed, then search
        await page.goto(f"https://www.grepool.com/it/catalogsearch/result/?q={encoded_sku}", wait_until="domcontentloaded", timeout=30000)
        
        # Wait for either product list or direct redirect
        try:
            await page.wait_for_selector('.product-item-info, .gallery-placeholder, .page-title', timeout=10000)
        except Exception:
            print(f"[{sku}] Timeout waiting for elements. Current URL: {page.url}")
            
        current_url = page.url
        print(f"[{sku}] Current URL: {current_url}")
        
        img_urls = []
        
        # If it's a search result page, click the first product
        product_items = await page.query_selector_all('.product-item-info a.product-item-photo')
        if product_items and 'catalogsearch' in current_url:
            print(f"[{sku}] Found search results, clicking first product...")
            href = await product_items[0].get_attribute('href')
            if href:
                await page.goto(href, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_selector('.gallery-placeholder img, .fotorama__img', timeout=10000)
        
        # Now we should be on the product page (or the only result page)
        print(f"[{sku}] Extracting images from product page...")
        
        # Wait a bit for JS gallery (fotorama) to load
        await page.wait_for_timeout(2000) 
        
        # Try finding high-res images in Fotorama gallery
        images = await page.query_selector_all('.fotorama__img')
        if not images:
            # Fallback for standard magento gallery
            images = await page.query_selector_all('.gallery-placeholder img, .product-image-photo')
            
        for img in images:
            src = await img.get_attribute('src')
            if src and 'loader' not in src: # Avoid loaders
                 img_urls.append(src)
                 
        # Deduplicate
        return list(set(img_urls))
        
    except Exception as e:
        print(f"[{sku}] Error: {e}")
        return []

async def main():
    df = pd.read_csv('prodotti_gre_mancanti.csv')
    skus_to_check = [clean_sku(s) for s in df['sku'].tolist() if clean_sku(s)]
    
    # Test batch
    test_batch = skus_to_check[:10]
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create context with standard user agent to avoid basic blocks
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Optional: accept cookies if banner blocks clicks
        # await page.goto('https://www.grepool.com/it/')
        # try: await page.click('#btn-cookie-accept', timeout=3000) except: pass
        
        for sku in test_batch:
            images = await search_and_extract(page, sku)
            results[sku] = images
            print(f"[{sku}] Found {len(images)} images.")
            
        await browser.close()
        
    with open('gre_images_test_pw.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("\nTest completed. Results saved to gre_images_test_pw.json")

if __name__ == "__main__":
    asyncio.run(main())
