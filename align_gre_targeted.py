
import asyncio
import pandas as pd
import json
import base64
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

def decrypt_url(encoded_str):
    try:
        missing_padding = len(encoded_str) % 4
        if missing_padding:
            encoded_str += '=' * (4 - missing_padding)
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            missing_padding = len(clean_b64) % 4
            if missing_padding:
                clean_b64 += '=' * (4 - missing_padding)
            return base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
    except: pass
    return None

async def run_alignment():
    # 1. Load Shopify Products
    shopify_file = 'jollygame-importer/jollygame-importer/shopify_gre_products.json'
    if not os.path.exists(shopify_file):
        print("Shopify products file not found.")
        return
    
    with open(shopify_file, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)
    
    sku_to_product = {}
    for p in shopify_products:
        for v in p['variants']['nodes']:
            if v['sku']:
                sku_to_product[v['sku'].strip().upper()] = p

    # 2. Load Mapping CSV
    csv_path = "mapping_prodotti_jolly_gre_FINALE.csv"
    df = pd.read_csv(csv_path)
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Focus on a few products including Sumatra which we know might have it
        target_skus = ["KPEOV5027", "KITPROV6188WO", "KIT500GY", "KITPR358GY"]
        test_df = df[df['SKU'].isin(target_skus)]
        
        print(f"🚀 Analyzing {len(test_df)} target products...")
        
        for index, row in test_df.iterrows():
            sku = str(row['SKU']).strip().upper()
            url = row['Grepool_URL']
            print(f"Analyzing SKU: {sku} - URL: {url}")
            
            jolly_link = None
            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(5000)
                
                # Check for JollyGame link in DOM (pre-rendered or already open)
                jolly_link = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                    const jolly = links.find(a => a.href.includes('storename=jollygame'));
                    return jolly ? jolly.href : null;
                }''')
                
                if not jolly_link:
                    # Try to open modal
                    # Look for button with specific classes or text
                    btn_selectors = [
                        "button.js-openModal", 
                        "button:has-text('Acquista')", 
                        "button:has-text('Dove acquistare')",
                        ".product-buy button"
                    ]
                    for sel in btn_selectors:
                        btn = page.locator(sel).first
                        if await btn.is_visible():
                            print(f"  Clicking button: {sel}")
                            await btn.click()
                            await page.wait_for_timeout(5000)
                            # Check again
                            jolly_link = await page.evaluate('''() => {
                                const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                                const jolly = links.find(a => a.href.includes('storename=jollygame'));
                                return jolly ? jolly.href : null;
                            }''')
                            if jolly_link: break
                
                if not jolly_link:
                    # Final attempt: wait longer and search for ANY link
                    await page.wait_for_timeout(5000)
                    jolly_link = await page.evaluate('''() => {
                        const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                        const jolly = links.find(a => a.href.includes('storename=jollygame'));
                        return jolly ? jolly.href : null;
                    }''')
            except Exception as e:
                print(f"  Error: {e}")
            
            decoded_url = None
            suggested_handle = None
            if jolly_link:
                try:
                    params = dict([p.split('=') for p in jolly_link.split('?')[1].split('&') if '=' in p])
                    encoded = params.get('store-redirect-url')
                    if encoded:
                        decoded_url = decrypt_url(encoded)
                        if decoded_url and "jollygame.it" in decoded_url:
                            path = decoded_url.split("jollygame.it/")[-1]
                            slug = path.split("/")[-1].replace(".html", "")
                            suggested_handle = slug
                            print(f"  [SUCCESS] Found Link: {decoded_url} -> Suggested Handle: {slug}")
                except: pass
            else:
                print("  [INFO] JollyGame link not found.")

            # Match with Shopify
            shopify_p = sku_to_product.get(sku)
            current_handle = shopify_p['handle'] if shopify_p else "NOT FOUND"
            
            results.append({
                "SKU": sku,
                "Grepool_URL": url,
                "Gre_Popup_URL": decoded_url,
                "Suggested_Handle": suggested_handle,
                "Shopify_Current_Handle": current_handle
            })
            
        await browser.close()

    res_df = pd.DataFrame(results)
    print("\nResults:")
    print(res_df)

if __name__ == "__main__":
    asyncio.run(run_alignment())
